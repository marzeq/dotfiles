#!/bin/bash
cd $HOME/.config/nvim/after/queries/mconf

git clone --depth 1 https://github.com/marzeq/tree-sitter-mconf.git _repo
mv _repo/queries/mconf/* .
rm -rf _repo
