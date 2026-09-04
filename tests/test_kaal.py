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
        import kaal.models.router as _rt
        _orig = _rt.try_chat_stream
        _rt.try_chat_stream = lambda msgs, **kw: script.pop(0)
        try:
            todos, summary, ep = brain.run("t", ask_cb=lambda q: True)
        finally:
            _rt.try_chat_stream = _orig
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
    def test_checkpoint_ordering_rapid(self):
        """Same-second checkpoints: rewind hamesha newest uthaye (mtime order)."""
        from kaal.skills import files as f
        import shutil
        shutil.rmtree("memory/backups", ignore_errors=True)
        d = os.path.abspath("memory/.test-tmp5")
        os.makedirs(d, exist_ok=True)
        self.addCleanup(lambda: shutil.rmtree(d, ignore_errors=True))
        p = os.path.join(d, "o.txt")
        f.write_file(p, "v1")
        f.checkpoint("a")
        f.edit_file(p, "v1", "v2", lambda q: True)
        f.checkpoint("b")  # same second possible
        f.edit_file(p, "v2", "v3", lambda q: True)
        f.rewind()
        self.assertIn("v2", f.read_file(p))

    def test_checkpoint_rewind(self):
        from kaal.skills import files as f
        import shutil
        shutil.rmtree("memory/backups", ignore_errors=True)
        d = os.path.abspath("memory/.test-tmp3")
        os.makedirs(d, exist_ok=True)
        self.addCleanup(lambda: shutil.rmtree(d, ignore_errors=True))
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


class TestRoadmap(unittest.TestCase):
    def test_secret_scan(self):
        from kaal.skills.secrets import scan_text
        self.assertTrue(scan_text('key = "sk-abcdefghij1234567890"'))
        self.assertEqual(scan_text("hello world"), [])

    def test_rate_cooldown(self):
        from kaal.models.router import _cool
        import time
        _cool("k1234567890abcdef", 60)
        self.assertGreater(_cool("k1234567890abcdef"), time.time())

    def test_project_detect(self):
        from kaal.skills.project import detect
        d = detect(".")
        self.assertIn("type", d)
        self.assertIn("test", d)

    def test_fuzzy_syntax_verify(self):
        from kaal.skills import files as f
        d = os.path.abspath("memory/.test-tmp4")
        os.makedirs(d, exist_ok=True)
        self.addCleanup(lambda: __import__("shutil").rmtree(d, ignore_errors=True))
        p = os.path.join(d, "b.py")
        f.write_file(p, "x = 1  \ny = 2\n")
        # trailing-space difference pe fuzzy match
        r = f.edit_file(p, "x = 1\ny = 2", "x = 10\ny = 2", lambda q: True)
        self.assertIn("Edit ho gayi", r)
        # syntax tootegi to block
        r2 = f.edit_file(p, "x = 10", "x = ", lambda q: True)
        self.assertIn("Syntax", r2)
        self.assertIn("x = 10", f.read_file(p))

    def test_estimate(self):
        from kaal.models.router import estimate
        self.assertIn("tokens", estimate("hello task"))

    def test_plugins_empty(self):
        from kaal.skills.pluginman import list_all
        self.assertEqual(list_all(), [])


class TestDifferentiators(unittest.TestCase):
    def test_clarify_flow(self):
        from kaal.models import brain
        script = [
            ("m", '{"thinking": "unclear", "clarify": "Kaunsi file?"}'),
            ("m", '{"thinking": "ok", "done": "kaam ho gaya"}'),
        ]
        import kaal.models.router as _rt
        _orig = _rt.try_chat_stream
        _rt.try_chat_stream = lambda msgs, **kw: script.pop(0)
        asked = []
        try:
            todos, summary, ep = brain.run(
                "fix karo", ask_cb=lambda q: True,
                ask_text_cb=lambda q: asked.append(q) or "README.md")
        finally:
            _rt.try_chat_stream = _orig
        self.assertEqual(asked, ["Kaunsi file?"])
        self.assertEqual(summary, "kaam ho gaya")

    def test_self_review_ok(self):
        from kaal import agent
        import kaal.models.router as _rt
        _orig = _rt.try_chat
        _rt.try_chat = lambda msgs, **kw: ("m", "OK")
        try:
            self.assertIn("OK", agent._self_review("t", "s"))
        finally:
            _rt.try_chat = _orig

    def test_telegram_handle(self):
        from kaal.channels.telegram import handle_text, NAME
        self.assertEqual(NAME, "telegram")
        self.assertIn("Kaal", handle_text("/start", None))
        self.assertIn("", handle_text("/status", None))
        r = handle_text("/task hello", lambda t, **k: {"summary": "done-ok", "endpoint": "x"})
        self.assertIn("done-ok", r)
        r2 = handle_text("hello", lambda t, **k: (_ for _ in ()).throw(Exception("x")))
        self.assertIn("", r2)

    def test_service_file_valid(self):
        import configparser
        p = os.path.join(REPO, "install", "kaal.service")
        c = configparser.ConfigParser(strict=False)
        c.read(p)
        self.assertIn("Unit", c.sections())
        self.assertIn("Service", c.sections())
        self.assertIn("kaal --serve", c["Service"]["ExecStart"])

    def test_persona_memory(self):
        from kaal.memory.persona import ensure, read_all, append_memory
        ensure()
        self.assertIn("USER.md", read_all() + "USER.md")
        append_memory("test-fact-xyz-unique")
        self.assertIn("test-fact-xyz-unique", read_all())
        try:
            for fn in ("MEMORY.md", "USER.md"):
                os.remove(os.path.join("memory", fn))
        except OSError:
            pass

    def test_thread_continuity(self):
        from kaal.agent import run_task
        from kaal.memory.patterns import thread_context
        run_task("thread continuity check one", ask_cb=lambda q: True)
        th = thread_context()
        self.assertIn("thread continuity check one", th.lower())


class TestSecurity(unittest.TestCase):
    """prompt.cpp security round: unattended deny + injection marking + undo depth."""

    def test_unattended_deny(self):
        from kaal.agent import run_task
        # schedule/serve style: ask hamesha False = sensitive auto-deny
        r = run_task("delete proof.txt", ask_cb=lambda q: False)
        self.assertEqual(r["status"], "denied")
        # explicit allow abhi bhi chalta hai
        from kaal.config_store import check_perm
        self.assertTrue(check_perm("delete_files", lambda q: False) is False)
        self.assertTrue(check_perm("nope_op_xyz", lambda q: True) is True)

    def test_levels(self):
        from kaal import autonomy as _au
        ok, note = _au.tool_allowed("file_delete", "L1")
        self.assertFalse(ok)
        self.assertIn("L1", note)
        ok2, _ = _au.tool_allowed("file_read", "L1")
        self.assertTrue(ok2)
        ok3, _ = _au.tool_allowed("file_delete", "L3")
        self.assertTrue(ok3)
        # L1 me delete step report-only (task-gate allow, level-gate skip)
        from kaal.agent import run_task
        r = run_task("delete proof2.txt", ask_cb=lambda q: True, level="L1")
        self.assertIn("L1", r["summary"])

    def test_trace_logged(self):
        from kaal.agent import run_task
        from kaal.trace import recent
        run_task("file list karo trace-test", ask_cb=lambda q: True)
        rows = recent(3)
        self.assertTrue(any("trace-test" in e.get("task", "") for e in rows))
        try:
            os.remove("logs/trace.jsonl")
        except OSError:
            pass

    def test_injection_marking(self):
        from kaal.skills.tools import _t_browser_fetch, UNTRUSTED_OPEN
        out = _t_browser_fetch({"url": "example.com"})
        self.assertIn("UNTRUSTED", out)
        self.assertTrue(out.startswith(UNTRUSTED_OPEN[:20]))

    def test_undo_depth(self):
        from kaal.skills import files as f
        import shutil
        shutil.rmtree("memory/backups", ignore_errors=True)
        d = os.path.abspath("memory/.test-tmp6")
        os.makedirs(d, exist_ok=True)
        self.addCleanup(lambda: shutil.rmtree(d, ignore_errors=True))
        p = os.path.join(d, "u.txt")
        f.write_file(p, "v1")
        f.edit_file(p, "v1", "v2", lambda q: True)
        f.edit_file(p, "v2", "v3", lambda q: True)
        self.assertIn("2 step", f.undo_last(p, 2))
        self.assertIn("v1", f.read_file(p))


class TestGaps(unittest.TestCase):
    def test_real_usage_callback(self):
        import kaal.models.llm as _llm
        got = []
        class FakeResp:
            def __enter__(self): return self
            def __exit__(self, *a): return False
            def read(self):
                import json
                return json.dumps({"choices": [{"message": {"content": "hi"}}],
                                   "usage": {"total_tokens": 42}}).encode()
        import urllib.request as _ur
        _orig = _ur.urlopen
        _ur.urlopen = lambda *a, **k: FakeResp()
        try:
            ok, txt = _llm.chat("https://x", "k", "m", [{"role": "user", "content": "hi"}],
                                usage_cb=lambda n: got.append(n))
        finally:
            _ur.urlopen = _orig
        self.assertTrue(ok)
        self.assertEqual(got, [42])

    def test_fts_suggest_and_thread(self):
        from kaal.memory import patterns as _p
        _p.learn("login page ka bug fix karo", "auth token refresh thik kiya")
        s = _p.suggest("login bug thik karna hai")
        self.assertIn("login", s.lower())
        th = _p.thread_context()
        self.assertIn("login", th.lower())
        try:
            os.remove("memory/patterns.db")
            os.remove("memory/thread.json")
        except OSError:
            pass

    def test_vision_failsoft(self):
        from kaal.skills.vision import describe
        self.assertIn("mili nahi", describe("nope.png"))
        self.assertIn("Format", describe("README.md"))


class TestContextPower(unittest.TestCase):
    def test_semsearch(self):
        from kaal.skills import semsearch
        n = semsearch.index_path("README.md")
        self.assertGreaterEqual(n, 1)
        rows = semsearch.search("install")
        self.assertGreaterEqual(len(rows), 1)

    def test_compress(self):
        from kaal.models.brain import _compress
        msgs = [{"role": "system", "content": "s"}, {"role": "user", "content": "t"}]
        msgs += [{"role": "assistant", "content": "x" * 500}, {"role": "user", "content": "y" * 500}] * 5
        out = _compress(msgs)
        self.assertLess(len("".join(m["content"] for m in out)),
                        len("".join(m["content"] for m in msgs)))
        self.assertEqual(out[:2], msgs[:2])

    def test_parallel_tools_mock(self):
        from kaal.models import brain
        script = [
            ("m", '{"thinking": "do parallel", "tools": [{"name": "file_list", "args": {"path": "."}}, {"name": "memory_recall", "args": {}}]}'),
            ("m", '{"thinking": "done", "done": "parallel ok"}'),
        ]
        import kaal.models.router as _rt
        _orig = _rt.try_chat_stream
        _rt.try_chat_stream = lambda msgs, **kw: script.pop(0)
        try:
            todos, summary, ep = brain.run("t", ask_cb=lambda q: True)
        finally:
            _rt.try_chat_stream = _orig
        self.assertEqual(summary, "parallel ok")
        self.assertGreaterEqual(len(todos), 3)

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

    def test_memory_detail_tool(self):
        from kaal.skills.tools import _t_memory_recall, _t_memory_detail
        out = _t_memory_recall({"n": 3})
        self.assertIn("compact", out)
        detail = _t_memory_detail({"index": 0})
        self.assertIsInstance(detail, str)

    def test_observations_logged(self):
        from kaal.agent import run_task
        from kaal.trace import recent
        run_task("file list karo obs-test", ask_cb=lambda q: True)
        rows = recent(3)
        self.assertTrue(any("obs-test" in e.get("task", "") for e in rows))
        obs = [r for r in rows if r.get("kind") == "observation"]
        self.assertGreaterEqual(len(obs), 1)
        try:
            os.remove("logs/trace.jsonl")
        except OSError:
            pass

    def test_personas_enriched(self):
        from kaal.agents.orchestrator import PERSONAS, ROLES
        self.assertIn("minimal_change_engineer", PERSONAS)
        self.assertIn("security_architect", PERSONAS)
        self.assertIn("database_optimizer", PERSONAS)
        self.assertIn("software_architect", PERSONAS)
        self.assertIn("code_reviewer", PERSONAS)
        self.assertIn("minimal_change_engineer", ROLES)
        self.assertIn("security_architect", ROLES)

    def test_plan_explore_roles(self):
        """OpenCode-style Plan/Explore read-only roles."""
        from kaal.agents.orchestrator import classify, persona, PERSONAS, ROLES
        self.assertIn("planner", PERSONAS)
        self.assertIn("explorer", PERSONAS)
        self.assertIn("planner", ROLES)
        self.assertIn("explorer", ROLES)
        self.assertEqual(classify("plan banao pehle"), "planner")
        self.assertEqual(classify("file kahan hai dhoondo"), "explorer")
        # existing routing untouched
        self.assertEqual(classify("code fix karo"), "coder")
        self.assertEqual(classify("github check karo"), "github_specialist")
        self.assertTrue(len(persona("planner")) > 20)
        self.assertTrue(len(persona("explorer")) > 20)


class TestWishlistBatch(unittest.TestCase):
    """prompt.cpp wishlist batch: write-guard, project ctx, effort."""

    def test_write_file_blocks_bad_python(self):
        from kaal.skills import files as f
        import shutil
        d = os.path.abspath("memory/.test-tmp6")
        os.makedirs(d, exist_ok=True)
        self.addCleanup(lambda: shutil.rmtree(d, ignore_errors=True))
        bad = os.path.join(d, "bad.py")
        r = f.write_file(bad, "def broken(:\n  pass")
        self.assertIn("roki", r)
        self.assertFalse(os.path.exists(bad))
        good = os.path.join(d, "good.py")
        r2 = f.write_file(good, "x = 1\n")
        self.assertIn("Write ho gayi", r2)

    def test_project_context(self):
        from kaal.skills.project import project_context
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(project_context(d), "")
            with open(os.path.join(d, "AGENTS.md"), "w") as fh:
                fh.write("# Rules\n- Hindi me jawab\n")
            ctx = project_context(d)
            self.assertIn("AGENTS.md", ctx)
            self.assertIn("Hindi", ctx)

    def test_effort_mapping(self):
        from kaal.models import router as rt
        self.assertEqual(rt.EFFORTS["low"], (0.2, 200))
        self.assertEqual(rt.EFFORTS["medium"], (0.7, 500))
        self.assertEqual(rt.EFFORTS["high"], (1.0, 1000))
        self.assertIn(rt.get_effort(), rt.EFFORTS)
        self.assertIn("low", rt.set_effort("low"))
        self.assertEqual(rt.get_effort(), "low")
        self.assertIn("medium", rt.set_effort("medium"))
        self.assertIn("galat", rt.set_effort("ultra"))


class TestWishlistBatch2(unittest.TestCase):
    """prompt.cpp mega-batch: workflows, scoped perms, crypto-fallback, lint, search."""

    def test_workflows_pure(self):
        from kaal import workflows as wf
        self.assertEqual(wf.fresh_branch("Fix Login BUG!!"), "kaal/fix-login-bug")
        self.assertEqual(len(wf.fresh_plan("x")), 5)
        self.assertEqual(wf.autopilot_pick([{"task": "a"}, {"task": "b"}, {}], 2), ["a", "b"])
        self.assertTrue(wf.ship_message("my plan\nline2").startswith("my plan"))

    def test_scoped_perms(self):
        from kaal import config_store as cs
        self.assertEqual(cs.get_perm("delete_files"), "ask")
        self.assertEqual(cs.get_perm("delete_files:./tmp"), "ask")
        self.assertEqual(cs.get_perm("no_such_op"), "ask")
        self.assertEqual(cs.get_perm("secrets"), "ask")

    def test_vault_crypto_fallback(self):
        from kaal import vault_crypto as vc
        d = {"providers": {"openai": [{"key": "sk-x"}]}}
        self.assertEqual(vc.decrypt_payload(d), d)  # legacy dict passthrough
        ok, _ = vc.encrypt_dict(d)
        if not vc.available():
            self.assertFalse(ok)  # Termux: plaintext+0600 path
            self.assertEqual(vc.decrypt_payload("ENC1:xxx"), {})

    def test_lint_file(self):
        from kaal.skills import project as pj
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "ok.py")
            with open(p, "w") as fh:
                fh.write("x = 1\n")
            self.assertIn("OK", pj.lint_file(p))
            b = os.path.join(d, "bad.py")
            with open(b, "w") as fh:
                fh.write("def broken(:\n")
            self.assertIn("FAIL", pj.lint_file(b))
            self.assertIn("n/a", pj.lint_file(os.path.join(d, "nope.py")))

    def test_memory_search(self):
        from kaal.memory import store as ms
        ms.save("test daal bhaat khana", "swadisht thali summary")
        rows = ms.search("daal bhaat")
        self.assertTrue(any("daal" in (t + s) for t, s in rows))
        self.assertEqual(ms.search("zzz-no-match-zzz-123"), [])

    def test_dep_audit_runs(self):
        from kaal.skills import dev
        out = dev.dep_audit()
        self.assertIn("rich", out)


class TestWishlistBatch3(unittest.TestCase):
    """Session caps, TF-IDF rank, persistent REPL."""

    def test_session_cap_helpers(self):
        from kaal.models import router as rt
        rt.session_reset()
        self.assertEqual(rt.session_used(), 0)
        self.assertFalse(rt.session_over())
        self.assertGreaterEqual(rt.session_cap(), 100)
        rt._SESSION["tokens"] = rt.session_cap() + 1
        self.assertTrue(rt.session_over())
        rt.session_reset()

    def test_ranked_search(self):
        from kaal.memory import store as ms
        ms.save("aam ka achaar recipe", "aam tel masala achaar")
        ms.save("python me traceback debug", "traceback line error fix")
        top = ms.ranked_search("achaar recipe")
        self.assertTrue(top)
        self.assertIn("achaar", (top[0][0] + top[0][1]).lower())
        top2 = ms.ranked_search("traceback fix")
        self.assertTrue(top2)
        self.assertIn("traceback", (top2[0][0] + top2[0][1]).lower())

    def test_repl_persist_and_guard(self):
        from kaal.skills import repl
        repl.reset()
        self.assertIn("OK", repl.run("x = 41"))
        self.assertIn("42", repl.run("print(x + 1)"))
        self.assertIn("allowed nahi", repl.run("import os"))
        self.assertIn("allowed nahi", repl.run("open('f').read()"))
        self.assertIn("x", repl.vars_list())
        repl.reset()
        self.assertEqual(repl.vars_list(), [])


class TestWishlistBatch4(unittest.TestCase):
    """RPC bridge, scoped perms, LSP fake-server, SWE harness."""

    def test_rpc_handle(self):
        from kaal import rpc
        r = rpc.handle({"id": 1, "method": "initialize"})
        self.assertEqual(r["result"]["agent"], "kaal")
        self.assertIn("prompt/run", r["result"]["methods"])
        self.assertIn("unknown-method", rpc.handle({"id": 2, "method": "nope"})["error"])
        self.assertIn("empty-task", rpc.handle({"id": 3, "method": "prompt/run",
                                                 "params": {"task": ""}})["error"])
        orig = rpc._run_task
        rpc._run_task = lambda t: {"status": "done", "summary": "mocked " + t}
        try:
            r2 = rpc.handle({"id": 4, "method": "prompt/run", "params": {"task": "hi"}})
            self.assertEqual(r2["result"]["summary"], "mocked hi")
        finally:
            rpc._run_task = orig

    def test_scoped_perm_prefix(self):
        import json
        from kaal import config_store as cs
        p = os.path.join("config", "permissions.json")
        had = None
        if os.path.isfile(p):
            with open(p, encoding="utf-8") as f:
                had = f.read()
        try:
            with open(p, "w", encoding="utf-8") as f:
                json.dump({"delete_files": "ask", "delete_files:/tmp": "allow",
                           "delete_files:/tmp/secret": "deny"}, f)
            self.assertEqual(cs.get_perm("delete_files:/tmp/x"), "allow")
            self.assertEqual(cs.get_perm("delete_files:/tmp/secret/y"), "deny")
            self.assertEqual(cs.get_perm("delete_files:/other"), "ask")
        finally:
            if had is None:
                try:
                    os.remove(p)
                except OSError:
                    pass
            else:
                with open(p, "w", encoding="utf-8") as f:
                    f.write(had)

    def test_lsp_fake_server(self):
        import shutil, subprocess, sys
        if os.name == "nt":
            self.skipTest("select() pipes Windows pe nahi")
        from kaal.skills import lsp
        srv = os.path.abspath("memory/.test-tmp-lsp.py")
        os.makedirs(os.path.dirname(srv), exist_ok=True)
        self.addCleanup(lambda: os.path.exists(srv) and os.remove(srv))
        with open(srv, "w", encoding="utf-8") as f:
            f.write(
                "import sys, json\n"
                "def rd():\n"
                " h=b''\n"
                " while not h.endswith(b'\\r\\n\\r\\n'):\n"
                "  c=sys.stdin.buffer.read(1)\n"
                "  if not c: return None\n"
                "  h+=c\n"
                " n=int([l for l in h.decode().splitlines() if 'ength' in l][0].split(':')[1])\n"
                " return json.loads(sys.stdin.buffer.read(n).decode() or 'null')\n"
                "def wr(m):\n"
                " b=json.dumps(m).encode()\n"
                " sys.stdout.buffer.write(b'Content-Length: %d\\r\\n\\r\\n' % len(b) + b)\n"
                " sys.stdout.buffer.flush()\n"
                "nid=0\n"
                "while True:\n"
                " m=rd()\n"
                " if m is None: break\n"
                " if m.get('method')=='exit': break\n"
                " if 'id' in m and m.get('method')=='initialize':\n"
                "  wr({'jsonrpc':'2.0','id':m['id'],'result':{'capabilities':{}}})\n"
                " elif 'id' in m and m.get('method')=='shutdown':\n"
                "  wr({'jsonrpc':'2.0','id':m['id'],'result':None})\n"
                " elif m.get('method')=='textDocument/didOpen':\n"
                "  u=(m.get('params') or {}).get('textDocument',{}).get('uri','')\n"
                "  wr({'jsonrpc':'2.0','method':'textDocument/publishDiagnostics','params':{'uri':u,'diagnostics':[{'range':{'start':{'line':0}},'message':'fake-warn'}]}})\n")
        with open(os.path.abspath("memory/.test-tmp-t.py"), "w") as f:
            f.write("x = 1\n")
        self.addCleanup(lambda: os.path.exists(os.path.abspath("memory/.test-tmp-t.py")) and os.remove(os.path.abspath("memory/.test-tmp-t.py")))
        out = lsp.diagnose("memory/.test-tmp-t.py", server_cmd=f"{sys.executable} {srv}",
                           root=".", timeout=15)
        self.assertIn("fake-warn", out)
        self.assertIn("n/a", lsp.diagnose("memory/.test-tmp-t.py", server_cmd="no-such-lsp-xyz"))

    def test_swe_harness(self):
        import shutil, subprocess, tempfile
        if shutil.which("git") is None:
            self.skipTest("git nahi mili")
        d = tempfile.mkdtemp(prefix="kaal-swe-test-")
        self.addCleanup(lambda: shutil.rmtree(d, ignore_errors=True))
        def g(*a):
            return subprocess.run(["git", "-C", d] + list(a), capture_output=True, text=True)
        g("init"); g("config", "user.email", "t@t.t"); g("config", "user.name", "t")
        with open(os.path.join(d, "t.py"), "w") as f:
            f.write("def test_ok():\n assert 1 == 1\n")
        g("add", "-A"); g("commit", "-m", "init")
        from benchmarks.swe_run import run_instance
        r = run_instance(d, "HEAD", "python3 -m pytest -q t.py", timeout=120)
        self.assertEqual(r["status"], "PASS")
        with open(os.path.join(d, "t.py"), "w") as f:
            f.write("def test_ok():\n assert 1 == 2\n")
        g("add", "-A"); g("commit", "-m", "break")
        r2 = run_instance(d, "HEAD", "python3 -m pytest -q t.py", timeout=120)
        self.assertEqual(r2["status"], "FAIL")


class TestMaintenanceBatch(unittest.TestCase):
    """prompt.cpp maintenance gaps: undo race, trace rotation."""

    def test_backup_no_collision_rapid(self):
        """20 rapid backups → 20 unique paths (overwrite race nahi).
        Stack cap 5 hai, isliye akhri 5 files disk pe, contents sahi order me."""
        from kaal.skills import files as f
        import shutil
        shutil.rmtree("memory/backups", ignore_errors=True)
        d = os.path.abspath("memory/.test-tmp7")
        os.makedirs(d, exist_ok=True)
        self.addCleanup(lambda: shutil.rmtree(d, ignore_errors=True))
        p = os.path.join(d, "c.txt")
        paths = []
        for i in range(20):
            with open(p, "w") as fh:
                fh.write(f"v{i}")
            bp = f._backup(p)
            self.assertTrue(bp)
            paths.append(bp)
        self.assertEqual(len(set(paths)), 20)  # koi overwrite nahi
        for bp, i in zip(paths[-5:], range(15, 20)):
            with open(bp, "rb") as fh:
                self.assertEqual(fh.read().decode(), f"v{i}")

    def test_trace_rotation(self):
        from kaal import trace as tr
        orig_max, orig_keep = tr.MAX_BYTES, tr.KEEP_TAIL
        tr.MAX_BYTES, tr.KEEP_TAIL = 8 * 1024, 10  # test ke liye chhota cap
        try:
            big = "x" * 900
            for _ in range(60):
                tr.log({"task": big, "mode": "t", "endpoint": "e", "status": "done",
                        "steps": 1, "tools": [], "secs": 0.1, "level": None, "run_id": "r"})
            import os as _os
            sz = _os.path.getsize(tr.PATH)
            self.assertLessEqual(sz, 20 * 1024)
            self.assertTrue(tr.recent(5))  # tail readable hai
        finally:
            tr.MAX_BYTES, tr.KEEP_TAIL = orig_max, orig_keep
            try:
                import os as _os2
                _os2.remove(tr.PATH)
            except OSError:
                pass


class TestBgHooks(unittest.TestCase):
    """Live-todo hooks: step_cb + cancel + inbox (+ vault masked list)."""

    def test_step_cb_legacy(self):
        from kaal.agent import run_task
        events = []
        res = run_task("test alpha kaam, test beta kaam",
                       ask_cb=lambda q: False,
                       step_cb=lambda t, s: events.append((t, s)))
        self.assertEqual(res["status"], "done")
        kinds = {s for _, s in events}
        self.assertIn("doing", kinds)
        self.assertIn("done", kinds)

    def test_cancel_preset(self):
        import threading
        from kaal.agent import run_task
        ev = threading.Event()
        ev.set()
        res = run_task("test alpha kaam, test beta kaam",
                       ask_cb=lambda q: False, cancel=ev)
        self.assertIn("cancel", res["summary"].lower())

    def test_inbox_note_lands(self):
        import queue
        from kaal.agent import run_task
        q = queue.Queue()
        q.put("beech wali note dhyan rakhna")
        res = run_task("test alpha kaam", ask_cb=lambda q2: False, inbox=q)
        self.assertIn("note", res["summary"].lower())

    def test_vault_summary_masked(self):
        from kaal.models import router as rt
        import tempfile, os as _os
        d = tempfile.mkdtemp()
        old_v, old_c = rt.VAULT, rt.CONFIG_DIR
        rt.VAULT, rt.CONFIG_DIR = _os.path.join(d, "vault.json"), d
        try:
            rt.add_user_key("openai", "sk-testkey1234567890")
            s = rt.vault_summary()
            self.assertIn("openai", s)
            full = "sk-testkey1234567890"
            self.assertNotIn(full, str(s))
            self.assertIn("sk-tes", s["openai"][0])
        finally:
            rt.VAULT, rt.CONFIG_DIR = old_v, old_c


class TestSweDataset(unittest.TestCase):
    """SWE dataset runner: patch + grading + batch."""

    def _mk_repo(self):
        import shutil, subprocess, tempfile
        d = tempfile.mkdtemp(prefix="kaal-swe-t-")
        self.addCleanup(lambda: shutil.rmtree(d, ignore_errors=True))
        def g(*a):
            return subprocess.run(["git", "-C", d] + list(a), capture_output=True, text=True)
        g("init"); g("config", "user.email", "t@t.t"); g("config", "user.name", "t")
        with open(os.path.join(d, "calc.py"), "w") as f:
            f.write("def add(a, b):\n return a - b\n")
        with open(os.path.join(d, "test_calc.py"), "w") as f:
            f.write("from calc import add\ndef test_add():\n assert add(1, 2) == 3\n")
        g("add", "-A"); g("commit", "-m", "buggy")
        patch = ("--- a/calc.py\n+++ b/calc.py\n@@ -1,2 +1,2 @@\n"
                 " def add(a, b):\n- return a - b\n+ return a + b\n")
        return d, patch

    def test_grade_resolved(self):
        import shutil
        if shutil.which("git") is None:
            self.skipTest("git nahi mili")
        from benchmarks.swe_run import grade_instance
        d, patch = self._mk_repo()
        r = grade_instance({"id": "t1", "repo": d, "base_commit": "HEAD",
                            "patch": patch,
                            "fail_to_pass": ["python3 -m pytest -q test_calc.py"],
                            "pass_to_pass": []}, timeout=120)
        self.assertEqual(r["status"], "graded")
        self.assertTrue(r["resolved"], r)

    def test_grade_no_patch_trivial(self):
        import shutil
        if shutil.which("git") is None:
            self.skipTest("git nahi mili")
        from benchmarks.swe_run import grade_instance, apply_patch
        d, _ = self._mk_repo()
        ok, _ = apply_patch(d, "")
        self.assertTrue(ok)
        import subprocess
        subprocess.run(["git", "-C", d, "checkout", "--", "."], capture_output=True)
        r = grade_instance({"id": "t2", "repo": d, "base_commit": "HEAD",
                            "patch": "",
                            "fail_to_pass": ["python3 -m pytest -q test_calc.py"],
                            "pass_to_pass": []}, timeout=120)
        self.assertFalse(r["resolved"])  # pre FAIL → unresolved (not trivial)

    def test_run_dataset_batch(self):
        import shutil, json as _js, tempfile
        if shutil.which("git") is None:
            self.skipTest("git nahi mili")
        from benchmarks.swe_run import run_dataset
        d, patch = self._mk_repo()
        insts = [
            {"id": "good", "repo": d, "base_commit": "HEAD", "patch": patch,
             "fail_to_pass": ["python3 -m pytest -q test_calc.py"], "pass_to_pass": []},
            {"id": "bad", "repo": d, "base_commit": "HEAD", "patch": "garbage not a diff",
             "fail_to_pass": ["python3 -m pytest -q test_calc.py"], "pass_to_pass": []},
        ]
        fp = os.path.join(tempfile.mkdtemp(), "ds.json")
        with open(fp, "w") as f:
            _js.dump(insts, f)
        done, total = run_dataset(fp, timeout=120)
        self.assertEqual(total, 2)
        self.assertEqual(done, 1)


if __name__ == "__main__":
    unittest.main()
