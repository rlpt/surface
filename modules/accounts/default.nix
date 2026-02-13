{ pkgs }:

{
  name = "accounts";
  description = "Plain-text bookkeeping (hledger)";
  packages = with pkgs; [ hledger ];
}
