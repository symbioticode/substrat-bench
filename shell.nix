# shell.nix — Environnement reproductible pour banc-essai ETAU/SECS (NixOS 25.05)
{ pkgs ? import <nixpkgs> {} }:

pkgs.mkShell {
  packages = with pkgs.python312Packages; [
    python
    pip
    pytorch        # Framework PyTorch CPU pré-compilé
    transformers
    sentence-transformers
    scikit-learn
    matplotlib
    seaborn
    scipy
    pandas
    numpy
    pytest
    tqdm
    rich
    pyyaml
    openai
    anthropic
    tenacity
    python-dotenv
  ];

  shellHook = ''
    echo "✅ Environnement banc-essai ETAU/SECS activé"
    echo "   Python    : $(python --version)"
    echo "   PyTorch   : $(python -c 'import torch; print(torch.__version__)' 2>/dev/null || echo 'non chargé')"
    echo "   Transformers: $(python -c 'import transformers; print(transformers.__version__)' 2>/dev/null || echo 'non chargé')"
    echo "   SentenceTransformers: $(python -c 'import sentence_transformers; print(sentence_transformers.__version__)' 2>/dev/null || echo 'non chargé')"
  '';
}