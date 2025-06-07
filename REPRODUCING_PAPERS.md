# Reproducing papers results

## SubXPAT paper (in review) []()

The required flags for reproducing the results are:
- `--subxpat`
- `--input-max`/`--imax` with a value of `6`
- `--output-max`/`--omax` with a value of `3`
- `--max-lpp`/`--max-literals-per-product` with a value of `6`
- `--max-ppo`/`--max-products-per-output` with a value of `6`

### Example
```bash
python3 main.py CIRCUIT --max-error=ERROR --subxpat --imax=6 --omax=3 --max-lpp=6 --max-ppo=6
```
