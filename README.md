# Luau Obfuscator — advanced starter

Run:
`python3 obfuscator.py input.luau -o protected.luau`

This build is dependency-free and source-to-source. It removes comments, protects quoted strings, rewrites ordinary integer literals, and renames conservative local declarations without wrapping the entire script.

A real VM/compiler layer should be added only after extensive Luau compatibility tests. This project is not a Luraph clone.
