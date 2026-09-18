import pathlib

p = pathlib.Path("/home/pingu/github/deh-dbt-portifolio/Makefile")
text = p.read_text(encoding="utf-8")

old1 = '\t@echo "    make build-rede       \u2014 S\u00f3 modelos rede_social"\n\t@echo ""\n'
new1 = '\t@echo "    make build-rede       \u2014 S\u00f3 modelos rede_social"\n\t@echo "    make build-system     \u2014 S\u00f3 modelos system (request_log + app_log)"\n\t@echo ""\n'
assert text.count(old1) == 1, "help text anchor not found or not unique"
text = text.replace(old1, new1)

old2 = "build-rede:\n\t$(MAKE) build domain=rede_social\n\n# \u2500\u2500 Quality Gates"
new2 = "build-rede:\n\t$(MAKE) build domain=rede_social\n\nbuild-system:\n\t$(MAKE) build domain=system\n\n# \u2500\u2500 Quality Gates"
assert text.count(old2) == 1, "build target anchor not found or not unique"
text = text.replace(old2, new2)

p.write_text(text, encoding="utf-8")
print("OK")
