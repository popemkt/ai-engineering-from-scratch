{
  description = "ai-engineering-from-scratch — learning dev env (toolchain layer)";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";

  outputs = { self, nixpkgs }:
    let
      systems = [ "aarch64-darwin" "x86_64-darwin" "aarch64-linux" "x86_64-linux" ];
      forAll = f: nixpkgs.lib.genAttrs systems (s: f nixpkgs.legacyPackages.${s});
    in {
      devShells = forAll (pkgs: {
        default = pkgs.mkShell {
          # Toolchain only. Python LIBS (numpy/torch) come from uv, not nix.
          packages = [
            pkgs.python312
            pkgs.uv
            pkgs.nodejs_22
            pkgs.pnpm
            pkgs.git
          ];

          # UV_PYTHON pins uv to the nix interpreter. UV_PROJECT_ENVIRONMENT (.venv)
          # is set in .envrc where $PWD is reliably the repo root.
          shellHook = ''
            export UV_PYTHON="${pkgs.python312}/bin/python3.12"
          '';
        };
      });
    };
}
