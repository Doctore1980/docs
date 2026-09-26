"""Pruebas sin red de las herramientas deterministas de /investigar.

Ejecutar desde la carpeta de la skill:
    .venv/bin/python -m unittest discover -s tests -v

Las APIs externas se simulan sustituyendo `safe_get`; cada prueba fija un
fallo concreto que ya ocurrió en un expediente real.
"""

import json
import os
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tools"))

import research_tools as rt  # noqa: E402
import slide_generator as sg  # noqa: E402
import zotero_export as ze  # noqa: E402


class Resp:
    def __init__(self, status=200, payload=None, text=""):
        self.status_code = status
        self._payload = payload
        self.text = text

    def json(self):
        if self._payload is None:
            raise ValueError("sin JSON")
        return self._payload


def fake_get(routes):
    """routes: lista de (subcadena_url, respuesta | callable(url, params))."""
    def _get(url, params=None, **kwargs):
        for frag, resp in routes:
            if frag in url:
                return resp(url, params) if callable(resp) else resp
        return None
    return _get


EFETCH_RETRACTED = ("<PubmedArticleSet><PubmedArticle><PMID>1</PMID>"
                    "<PublicationType>Retracted Publication</PublicationType>"
                    "</PubmedArticle><PubmedArticle><PMID>2</PMID></PubmedArticle></PubmedArticleSet>")


class VerifyTests(unittest.TestCase):
    def run_verify(self, routes, ids):
        with mock.patch.object(rt, "safe_get", side_effect=fake_get(routes)), \
                mock.patch.object(rt.time, "sleep"):
            return rt.verify_identifiers(ids)

    def test_pmid_existente_retractado_e_inventado(self):
        esummary = Resp(payload={"result": {"1": {"title": "a"}, "2": {"title": "b"},
                                            "3": {"uid": "3", "error": "cannot get document summary"}}})
        out = self.run_verify([("esummary", esummary), ("efetch", Resp(text=EFETCH_RETRACTED))],
                              ["PMID:1", "PMID:2", "PMID:3"])
        self.assertEqual((out["PMID:1"]["exists"], out["PMID:1"]["retracted"]), (True, True))
        self.assertEqual((out["PMID:2"]["exists"], out["PMID:2"]["retracted"]), (True, False))
        self.assertIs(out["PMID:3"]["exists"], False)

    def test_ncbi_429_no_es_inventado(self):
        out = self.run_verify([("eutils", Resp(status=429))], ["PMID:1"])
        self.assertIsNone(out["PMID:1"]["exists"])
        self.assertIn("repetir verify", out["PMID:1"]["checked_against"])

    def test_fallo_de_retracciones_no_da_false(self):
        esummary = Resp(payload={"result": {"1": {"title": "a"}}})
        out = self.run_verify([("esummary", esummary), ("efetch", Resp(status=429))], ["PMID:1"])
        self.assertIs(out["PMID:1"]["exists"], True)
        self.assertIsNone(out["PMID:1"]["retracted"])

    def test_pmids_en_una_sola_peticion(self):
        llamadas = []

        def esummary(url, params):
            llamadas.append(params["id"])
            return Resp(payload={"result": {i: {"title": "t"} for i in params["id"].split(",")}})
        self.run_verify([("esummary", esummary), ("efetch", Resp(text=""))],
                        [f"PMID:{i}" for i in range(1, 30)])
        self.assertEqual(len(llamadas), 1)

    def test_doi_fuera_de_crossref(self):
        out = self.run_verify([("api.crossref.org", Resp(status=404)),
                               ("doi.org/api/handles", Resp(payload={"responseCode": 1}))],
                              ["DOI:10.22037/uj.v0i0.4758"])
        self.assertIs(out["DOI:10.22037/uj.v0i0.4758"]["exists"], True)
        self.assertIsNone(out["DOI:10.22037/uj.v0i0.4758"]["retracted"])

    def test_doi_inexistente(self):
        out = self.run_verify([("api.crossref.org", Resp(status=404)),
                               ("doi.org/api/handles", Resp(status=404, payload={"responseCode": 100}))],
                              ["DOI:10.9999/nada"])
        self.assertIs(out["DOI:10.9999/nada"]["exists"], False)

    def test_doi_con_apis_caidas(self):
        out = self.run_verify([], ["DOI:10.1/x"])
        self.assertIsNone(out["DOI:10.1/x"]["exists"])

    def test_nct(self):
        out = self.run_verify([("clinicaltrials.gov", Resp(status=404))], ["NCT:NCT00000001"])
        self.assertIs(out["NCT:NCT00000001"]["exists"], False)
        out = self.run_verify([("clinicaltrials.gov", Resp(status=503))], ["NCT:NCT00000001"])
        self.assertIsNone(out["NCT:NCT00000001"]["exists"])


class AuditFiguresTests(unittest.TestCase):
    CORPUS = {"PMID:1": "expulsion 45% (p=0·73)", "DOI:10.1/x": "n = 512 patients"}

    def test_citas_agrupadas_y_punto_medio(self):
        doc = "Tasa 45 % y p = 0,73 con n = 512 [PMID:1; DOI:10.1/x]."
        self.assertEqual(rt.audit_figures(doc, self.CORPUS)["n_cifras_sin_respaldo"], 0)

    def test_cifra_sin_respaldo_y_sin_cita(self):
        res = rt.audit_figures("Otra 99 % [PMID:1].\nSin cita 77 %.", self.CORPUS)
        self.assertEqual([c["cifra"] for c in res["cifras_a_cotejar"]], ["99 %", "77 %"])


class AbstractsTests(unittest.TestCase):
    def test_entidades_y_sin_truncar_a_1800(self):
        largo = "x " * 1500
        xml = (f"<PubmedArticle><PMID>1</PMID><AbstractText>p=0&#xb7;73 y p&lt;0.001 {largo}"
               f"CONCLUSION</AbstractText></PubmedArticle>")
        with mock.patch.object(rt, "safe_get", return_value=Resp(text=xml)), \
                mock.patch.object(rt.time, "sleep"):
            txt = rt.fetch_pubmed_abstracts(["1"])["1"]
        self.assertIn("p=0·73", txt)
        self.assertIn("p<0.001", txt)
        self.assertTrue(txt.endswith("CONCLUSION"))


class SearchStatusTests(unittest.TestCase):
    def test_fuente_caida_queda_registrada(self):
        routes = [("semanticscholar", Resp(status=429)), ("openalex", Resp(status=429)),
                  ("europepmc", Resp(payload={"resultList": {"result": []}})),
                  ("esearch", Resp(payload={"esearchresult": {"idlist": []}}))]
        with mock.patch.object(rt, "safe_get", side_effect=fake_get(routes)):
            rt.search_all("q")
        self.assertIn("429", rt.FUENTES_ESTADO["Semantic Scholar"])
        self.assertIn("429", rt.FUENTES_ESTADO["OpenAlex"])
        self.assertTrue(rt.FUENTES_ESTADO["Europe PMC"].startswith("ok"))


class ZoteroTests(unittest.TestCase):
    def test_autor_formato_ris(self):
        self.assertEqual(ze._ris_author("Campschroer T"), "Campschroer, T")
        self.assertEqual(ze._ris_author("van der Berg JH"), "van der Berg, JH")
        self.assertEqual(ze._ris_author("Smith, John"), "Smith, John")

    def test_doi_fuera_de_crossref_usa_doi_org(self):
        csl = Resp(payload={"title": "Tamsulosin MA", "container-title": "Urol J",
                            "issued": {"date-parts": [[2019]]}, "author": [{"family": "Tao", "given": "R"}]})
        with mock.patch.object(ze, "safe_get", side_effect=fake_get([("api.crossref.org", Resp(status=404)),
                                                                     ("doi.org/", csl)])):
            meta = ze.fetch_item_metadata("DOI:10.22037/uj.v0i0.4758")
        self.assertTrue(meta["complete"])
        self.assertEqual((meta["title"], meta["journal"], meta["year"]), ("Tamsulosin MA", "Urol J", "2019"))


class SlidesTests(unittest.TestCase):
    def test_sin_contenido_de_especialidad_ni_recortes(self):
        cuerpo = "\n".join(f"linea {i}" for i in range(30))
        ids = [f"PMID:{i}" for i in range(12)]
        md = sg.generate_marp_presentation({"pregunta": "¿Dapagliflozina en ERC?"}, {"nivel": "rapido"},
                                           f"## Evidencia\n{cuerpo}", ids, ["PubMed"])
        self.assertNotIn("Uro-Onco", md)
        self.assertIn("linea 29", md)
        self.assertIn("PMID:11", md)
        self.assertIn("**Fuentes Consultadas**: PubMed.", md)
        prompts = sg.generate_visual_prompts({"pregunta": "¿Dapagliflozina en ERC?"}, {})
        self.assertNotIn("prostate", prompts.lower())


class CliTests(unittest.TestCase):
    def test_corpus_combina_pubmed_y_candidatos(self):
        with tempfile.TemporaryDirectory() as d:
            v = os.path.join(d, "v.json")
            c = os.path.join(d, "c.json")
            with open(v, "w") as f:
                json.dump(["PMID:1", "DOI:10.1/x"], f)
            with open(c, "w") as f:
                json.dump({"candidatos": [{"identifier": "DOI:10.1/x", "abstract": "abs doi"}]}, f)
            argv = ["research_tools.py", "corpus", "--validos", v, "--candidatos", c]
            with mock.patch.object(sys, "argv", argv), \
                    mock.patch.object(rt, "fetch_pubmed_abstracts", return_value={"1": "abs pmid"}), \
                    mock.patch("sys.stdout", new_callable=lambda: __import__("io").StringIO()) as out:
                rt.main()
            self.assertEqual(json.loads(out.getvalue()), {"PMID:1": "abs pmid", "DOI:10.1/x": "abs doi"})


if __name__ == "__main__":
    unittest.main()
