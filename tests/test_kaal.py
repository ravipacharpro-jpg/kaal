"""Kaal test suite — stdlib unittest, zero deps. Run: repo root se
python3 -m unittest discover tests  (ya pytest). Cwd-independent: tmp repo root pe."""
import os, sys, unittest

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, REPO)
os.chdir(REPO)


class TestRouter(unittest.TestCase):
    def test_endpoints_20(self):
        from kaal.models.router import list_endpoints, select_endpoint
        self.assertGreaterEqual(len(list_endpoints()), 20)
        self.assertEqual(select_endpoint()["name"], "omniroute/auto")

    def test_no_keys_fallback(self):
        from kaal.models.router import try_llm
        self.assertEqual(try_llm("hi"), ("rule-based", ""))


class TestPermissions(unittest.TestCase):
    def test_deny_blocks(self):
        from kaal.agent import run_task
        r = run_task("delete x", ask_cb=lambda q: False)
        self.assertEqual(r["status"], "denied")


class TestFiles(unittest.TestCase):
    def test_write_edit_undo(self):
        from kaal.skills import files as f
        d = os.path.abspath("memory/.test-tmp")
        os.makedirs(d, exist_ok=True)
        self.addCleanup(lambda: __import__("shutil").rmtree(d, ignore_errors=True))
        p = os.path.join(d, "t.txt")
        f.write_file(p, "hello")
        self.assertIn("hello", f.read_file(p))
        r = f.edit_file(p, "hello", "world", lambda q: True)
        self.assertIn("Edit ho gayi", r)
        self.assertIn("world", f.read_file(p))
        u = f.undo_last(p)
        self.assertIn("Undo ho gaya", u)
        self.assertIn("hello", f.read_file(p))

    def test_outline_chunk(self):
        from kaal.skills import files as f
        d = os.path.abspath("memory/.test-tmp2")
        os.makedirs(d, exist_ok=True)
        self.addCleanup(lambda: __import__("shutil").rmtree(d, ignore_errors=True))
        p = os.path.join(d, "a.py")
        f.write_file(p, "def foo():\n pass\n" * 50)
        self.assertIn("foo", f.outline(p))
        self.assertIn("[lines 0-5/", f.read_file(p, 2000, 0, 5))


class TestSandbox(unittest.TestCase):
    def test_code_ok_and_block(self):
        from kaal.skills.code import run_python
        self.assertEqual(run_python("print(2+2)"), "4")
        self.assertIn("Block", run_python("import os; os.system('x')"))

    def test_code_ast_bypass_blocked(self):
        from kaal.skills.code import run_python
        # diagnose me mile bypass: arbitrary file read via open()
        self.assertIn("Block", run_python("print(open('x').read())"))
        self.assertIn("Block", run_python("getattr(__import__('o'+'s'),'sy'+'stem')('x')"))
        self.assertIn("Block", run_python("().__class__.__base__('x')"))
        self.assertIn("Block", run_python("eval('1')"))
        # legit code chalta hai
        self.assertEqual(run_python("x=[i*i for i in range(4)]\nprint(sum(x))"), "14")

    def test_shell_allowlist(self):
        from kaal.skills.shell import run
        self.assertEqual(run("echo hi", lambda q: True), "hi")
        self.assertIn("Block", run("rm -rf /", lambda q: True))
        self.assertIn("cancel", run("ls", lambda q: False))


class TestBrain(unittest.TestCase):
    def test_mock_loop(self):
        from kaal.models import brain
        script = [
            ("m", '{"thinking": "list", "tool": {"name": "file_list", "args": {"path": "."}}}'),
            ("m", '{"thinking": "done", "done": "ok mock"}'),
        ]
        brain.try_chat = lambda msgs, **kw: script.pop(0)
        todos, summary, ep = brain.run("t", ask_cb=lambda q: True)
        self.assertEqual(summary, "ok mock")
        self.assertEqual(ep, "m")


class TestOrchestrator(unittest.TestCase):
    def test_classify(self):
        from kaal.agents.orchestrator import decompose
        jobs = decompose("code fix karo aur github check karo")
        agents = {j["agent"] for j in jobs}
        self.assertIn("coder", agents)
        self.assertIn("github_specialist", agents)


class TestPower(unittest.TestCase):
    def test_checkpoint_rewind(self):
        from kaal.skills import files as f
        import shutil
        shutil.rmtree("memory/backups", ignore_errors=True)  # stale state hatao
        d = os.path.abspath("memory/.test-tmp3")
        os.makedirs(d, exist_ok=True)
        self.addCleanup(lambda: __import__("shutil").rmtree(d, ignore_errors=True))
        p = os.path.join(d, "c.txt")
        f.write_file(p, "v1")
        f.checkpoint("t")
        f.edit_file(p, "v1", "v2", lambda q: True)
        self.assertIn("v2", f.read_file(p))
        self.assertIn("Rewind", f.rewind())
        self.assertIn("v1", f.read_file(p))

    def test_plan_and_recipes(self):
        from kaal.planner import draft, write, read
        steps = draft("code fix karo aur test chalao")
        self.assertGreaterEqual(len(steps), 1)
        write("t", steps)
        self.assertIn("Plan", read())
        try:
            os.remove("PLAN.md")
        except OSError:
            pass
        from kaal.recipes import list_all, get
        self.assertIn("morning-review", list_all())
        self.assertGreaterEqual(len(get("morning-review")), 1)

    def test_local_skills(self):
        from kaal.skills import rules
        os.makedirs(".kaal/skills", exist_ok=True)
        with open(".kaal/skills/t.md", "w") as fh:
            fh.write("keywords: zaptest\n\nZap rule")
        self.addCleanup(lambda: __import__("shutil").rmtree(".kaal", ignore_errors=True))
        self.assertIn("Zap rule", rules.match("please zaptest now"))

    def test_changelog(self):
        from kaal.skills.git import changelog
        self.assertIn("Features", changelog(5))

    def test_export(self):
        from kaal.memory.store import save, export_md
        save("export test", "export summary")
        p = os.path.abspath("memory/.test-export.md")
        self.addCleanup(lambda: os.path.exists(p) and os.remove(p))
        self.assertIn("Export ho gaya", export_md(p))


class TestHonest(unittest.TestCase):
    """prompt.cpp diagnose ke fixes lock karo."""

    def test_personas_exist(self):
        from kaal.agents.orchestrator import PERSONAS, persona
        for a in ("coder", "researcher", "analyzer", "github_specialist"):
            self.assertIn(a, PERSONAS)
            self.assertTrue(len(persona(a)) > 20)

    def test_brain_keyless_ollama_path(self):
        from kaal.models import router
        # Ollama band + key nahi = rule-based (fail-soft, crash nahi)
        self.assertEqual(router.try_chat([{"role": "user", "content": "hi"}]),
                         ("rule-based", ""))
        self.assertIsInstance(router.brain_active(), bool)

    def test_smart_decompose_fallback_no_keys(self):
        from kaal.agents.orchestrator import decompose, classify_llm
        # key/Ollama nahi to keyword fallback, LLM call nahi
        self.assertEqual(classify_llm("code fix karo"), "coder")
        jobs = decompose("code fix karo aur github check karo", smart=True)
        self.assertEqual({j["agent"] for j in jobs}, {"coder", "github_specialist"})

    def test_safe_repo_outside_home(self):
        from kaal.skills.files import _safe
        # repo root ke andar hamesha safe (HOME chahe kuch bhi ho)
        self.assertIsNotNone(_safe("README.md"))
        # bahar ka path unsafe
        self.assertIsNone(_safe("/etc/passwd"))
        self.assertIsNone(_safe("../../etc/passwd"))

    def test_builtin_free_need_keys(self):
        from kaal.models.router import BUILTIN_FREE
        keyless = [e for e in BUILTIN_FREE if e["key"] in ("", "local")]
        # keyless hone ka matlab callable nahi — sirf ollama_local real hai
        self.assertIn("ollama_local", [e["name"] for e in keyless])


class TestCrossPlatform(unittest.TestCase):
    def test_role_models(self):
        from kaal.models.router import set_role_model, get_role_model
        set_role_model("architect", "auto")
        self.assertEqual(get_role_model("architect"), "auto")
        try:
            os.remove("config/model.json")
        except OSError:
            pass

    def test_sandbox_defaults_off(self):
        from kaal.skills.sandbox import enabled, available
        self.assertFalse(enabled())
        self.assertIsInstance(available(), bool)

    def test_platform_detect(self):
        from kaal.platform_adapt import detect, describe, data_dir
        self.assertIn(detect(), ("termux", "linux", "macos", "windows"))
        self.assertIn("Platform", describe())
        self.assertTrue(data_dir())

    def test_parallel_safe_order(self):
        from kaal.agent import run_task
        r = run_task("file list karo aur github repo check karo", ask_cb=lambda q: True)
        self.assertEqual(r["status"], "done")
        self.assertEqual(len(r["todos"]), 2)


if __name__ == "__main__":
    unittest.main()
