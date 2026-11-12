# Reproducibility and Refactoring Notes

## Provenance

The refactoring baseline is the latest pair of supplied files, preserved byte-for-byte under `archive/original/`. The two source files in the user's supplied folder were left untouched. The apartment layout image is included in `results/` for documentation. Old iteration photos are excluded from this repository.

## Differences found in the supplied materials

1. The manuscript defines a compliance-area ratio and reports maximizing lighting quality, but the baseline code compared post-conversion lux values with 0.5028–1.1173. Those values are 90/179 and 200/179, while the calculator already multiplies the photopic RGB value by 179 to return lux. The refactored objective compares against 90–200 lux, following the manuscript's stated 90% lower threshold and 200 lux upper threshold.
2. The manuscript specifies 20 inner iterations, cooling factor 0.6, and five major cycles. The latest supplied script instead had one proposal per temperature and one top-level run. An earlier archive had 20 proposals and five runs but used a different summed-error objective and a cooling factor of 0.8. The refactored defaults follow the manuscript's final experimental settings; the random seed is a new reproducibility aid and is recorded in the output.
3. The latest script's acceptance test was incompatible with maximizing compliance: it accepted every improving move, but also accepted every worsening move because `exp(-delta/T) > random` is always true for negative delta. The refactored Metropolis probability for a worsening move is `exp(delta/T)`.
4. The original candidate creation copied only each luminaire dictionary, leaving nested position lists shared with the current layout. A proposal could therefore mutate the incumbent before acceptance. Candidate layouts are now deeply copied.
5. The original neighbor selector never moved the standalone third luminaire, although it is part of the modeled seven-light layout. The refactored neighbor set includes this single-light move alongside the original mirrored-pair moves.
6. The paper's abstract and discussion describe energy reduction and its method section calls the objective multi-objective. Its displayed equation and code model only the compliant-area fraction, while count and luminaire flux remain fixed. This repository preserves the formal compliance objective and does not claim direct energy optimization or energy savings.

## Remaining limitations

- The exact Radiance version, command options beyond `rtrace -I -h -ab 2`, any random seed used for the reported paper results, and the final numeric optimized score/layout are not fully documented in the supplied paper or the latest source.
- Radiance was not available in the current environment, so no end-to-end lighting calculation or comparison to the paper's ~63% and >80% figures has been performed.
- The supplied legacy screenshots are not included in this repository.
- The paper says its original layout starts with approximately 63% compliance, but the exact layout file/output used for that value was not supplied as a structured result.
