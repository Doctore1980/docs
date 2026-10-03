"""Pruebas sin red de las herramientas deterministas de /investigar.

Ejecutar desde la carpeta de la skill:
    python3 -m unittest discover -s tests -v

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
import slide_generator  # noqa: E402,F401  (importa sin errores)
import zotero_export  # noqa: E402,F401


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
    """routes: lista de (subcadena_url, respuesta | callable(url, params, kwargs))."""
    def _get(url, params=None, **kwargs):
        for frag, resp in routes:
            if frag in url:
                return resp(url, params, kwargs) if callable(resp) else resp
        return None
    return _get


def patched(routes):
    return mock.patch.object(rt, "safe_get", side_effect=fake_get(routes))


EFETCH = ("<PubmedArticleSet><PubmedArticle><PMID>1</PMID>"
          "<PublicationType>Retracted Publication</PublicationType>"
          "</PubmedArticle><PubmedArticle><PMID>2</PMID></PubmedArticle></PubmedArticleSet>")


class VerifyTests(unittest.TestCase):
    def setUp(self):
        p = mock.patch.object(rt.time, "sleep")
        p.start()
        self.addCleanup(p.stop)

    def test_pmid_retractado_valido_y_no_encontrado(self):
        esummary = Resp(payload={"result": {"1": {"title": "a"}, "2": {"title": "b"},
                                            "3": {"error": "cannot get document summary"}}})
        with patched([("esummary", esummary), ("efetch", Resp(text=EFETCH))]):
            out = rt.verify_identifiers(["PMID:1", "PMID:2", "PMID:3"])
        self.assertEqual(out["PMID:1"]["estado"], "RETRACTADO")
        self.assertEqual(out["PMID:2"]["estado"], "VALIDO")
        self.assertEqual(out["PMID:3"]["estado"], "NO_ENCONTRADO")

    def test_429_de_ncbi_nunca_da_no_encontrado(self):
        # Ye 2017 se marcó como inventado por un 429: debe quedar INCONCLUSO.
        with patched([("eutils", Resp(status=429))]):
            out = rt.verify_identifiers(["PMID:29137830"])
        self.assertEqual(out["PMID:29137830"]["estado"], "INCONCLUSO")
        self.assertIsNone(out["PMID:29137830"]["exists"])

    def test_fallo_en_retractacion_no_da_valido(self):
        esummary = Resp(payload={"result": {"2": {"title": "b"}}})
        with patched([("esummary", esummary), ("efetch", Resp(status=503))]):
            out = rt.verify_identifiers(["PMID:2"])
        self.assertEqual(out["PMID:2"]["estado"], "INCONCLUSO")
        self.assertIsNone(out["PMID:2"]["retracted"])

    def test_doi_fuera_de_crossref_se_confirma_en_doi_org(self):
        routes = [("api.crossref.org/works/", Resp(status=404)),
                  ("doi.org/api/handles", Resp(status=200, payload={}))]
        with patched(routes):
            out = rt.verify_identifiers(["DOI:10.22037/uj.v0i0.4758"])
        v = out["DOI:10.22037/uj.v0i0.4758"]
        self.assertTrue(v["exists"])
        self.assertEqual(v["estado"], "INCONCLUSO")  # retractación no evaluable
        self.assertFalse(v["reintentable"])

    def test_doi_retractado_por_crossref(self):
        msg = {"message": {"updated-by": [{"type": "retraction", "DOI": "10.1016/x"}]}}
        with patched([("api.crossref.org/works/", Resp(payload=msg))]):
            out = rt.verify_identifiers(["DOI:10.1016/abc"])
        self.assertEqual(out["DOI:10.1016/abc"]["estado"], "RETRACTADO")


class GateTests(unittest.TestCase):
    def _caso(self, items):
        d = tempfile.mkdtemp()
        os.makedirs(os.path.join(d, "02-investigador"))
        with open(os.path.join(d, "02-investigador", "faceta-1.json"), "w") as fh:
            json.dump({"items": [{"identifier": i} for i in items]}, fh)
        return d

    def test_codigos_de_salida(self):
        casos = {
            0: {"estado": "VALIDO"},
            2: {"estado": "NO_ENCONTRADO"},
            3: {"estado": "INCONCLUSO"},
        }
        for codigo, v in casos.items():
            d = self._caso(["PMID:1"])
            fake = {"PMID:1": {**v, "detalle": ""}}
            with mock.patch.object(rt, "verify_identifiers", return_value=fake):
                _, got = rt.run_gate(d)
            self.assertEqual(got, codigo, v)
            with open(os.path.join(d, "_validos.json")) as fh:
                validos = json.load(fh)
            self.assertEqual(validos, ["PMID:1"] if codigo == 0 else [])

    def test_sin_identificadores_detiene(self):
        d = self._caso([])
        _, codigo = rt.run_gate(d)
        self.assertEqual(codigo, 2)


class SearchTests(unittest.TestCase):
    def test_fuente_con_429_queda_registrada(self):
        routes = [("esearch", Resp(payload={"esearchresult": {"idlist": []}})),
                  ("europepmc", Resp(payload={"resultList": {"result": []}})),
                  ("semanticscholar", Resp(status=429)),
                  ("openalex", Resp(status=429))]
        with patched(routes):
            rt.search_all("x")
        self.assertEqual(rt.FUENTES_ESTADO["PubMed"], "ok (0)")
        self.assertEqual(rt.FUENTES_ESTADO["Semantic Scholar"], "error: HTTP 429")
        self.assertEqual(rt.FUENTES_ESTADO["OpenAlex"], "error: HTTP 429")

    def test_claves_de_api_se_envian(self):
        vistos = {}

        def s2(url, params, kw):
            vistos["s2"] = kw.get("headers")
            return Resp(payload={"data": []})

        def oa(url, params, kw):
            vistos["oa"] = params
            return Resp(payload={"results": []})

        env = {"SEMANTIC_SCHOLAR_API_KEY": "k1", "OPENALEX_API_KEY": "k2"}
        with mock.patch.dict(os.environ, env), patched([("semanticscholar", s2), ("openalex", oa)]):
            rt.fetch_semantic_scholar("x")
            rt.fetch_openalex("x")
        self.assertEqual(vistos["s2"], {"x-api-key": "k1"})
        self.assertEqual(vistos["oa"]["api_key"], "k2")

    def test_abstract_pubmed_decodifica_entidades(self):
        xml = ("<PubmedArticle><PMID>5</PMID><AbstractText Label=\"R\">"
               "Mejoria significativa (p&lt;0.001) &amp; <i>HR</i> 0.61</AbstractText></PubmedArticle>")
        with patched([("efetch", Resp(text=xml))]), mock.patch.object(rt.time, "sleep"):
            out = rt.fetch_pubmed_abstracts(["5"])
        self.assertEqual(out["5"], "Mejoria significativa (p<0.001) & HR 0.61")

    def test_abstract_no_se_recorta_a_1800(self):
        texto = "a " * 2500
        xml = f"<PubmedArticle><PMID>6</PMID><AbstractText>{texto}</AbstractText></PubmedArticle>"
        with patched([("efetch", Resp(text=xml))]), mock.patch.object(rt.time, "sleep"):
            out = rt.fetch_pubmed_abstracts(["6"])
        self.assertGreater(len(out["6"]), 1800)


class TextoPlanoTests(unittest.TestCase):
    def test_no_borra_desigualdades_literales(self):
        self.assertEqual(rt._texto_plano("<h4>Results</h4>p<0.05 and HR>1"),
                         "Resultsp<0.05 and HR>1")


class CitasYCifrasTests(unittest.TestCase):
    def test_check_citations(self):
        doc = "Reduce eventos [PMID:1; DOI:10.1/AbC]. Otro dato (PMID: 9)."
        r = rt.check_citations(doc, ["PMID:1", "DOI:10.1/abc"])
        self.assertEqual(r["fuera_de_validos"], ["PMID:9"])

    def test_audit_figures(self):
        corpus = {"PMID:1": "HR 0.61 (95% CI 0.51-0.72) in 4304 patients"}
        doc = ("La dapagliflozina redujo el riesgo (HR 0,61) en 4.304 pacientes [PMID:1].\n"
               "Un 37% sin respaldo [PMID:1].\n"
               "Alrededor del 12% (pendiente de cotejo con la fuente).\n")
        r = rt.audit_figures(doc, corpus)
        self.assertEqual([c["cifra"] for c in r["coincidencias"]], ["0,61", "4.304"])
        self.assertEqual([c["cifra"] for c in r["cifras_a_cotejar"]], ["37%"])
        self.assertEqual([c["cifra"] for c in r["marcadas_pendiente_cotejo"]], ["12%"])


if __name__ == "__main__":
    unittest.main()
