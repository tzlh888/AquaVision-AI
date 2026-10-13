# AquaVision AI — Technical Interview Preparation

## 1. What was the actual prediction target?

Pixel-level classes derived from processed NASA CyAN `CI_cyano` digital numbers: 0–99 Low, 100–199 Moderate, and 200–253 High; 254/255 are invalid or masked. These are satellite proxy classes, not toxin concentration or laboratory truth.

## 2. Why were historical High pixels not enough?

Pixels within a patch share space, source imagery, and often the same 300 m CyAN cell. The legacy public artifacts lacked real footprint, scene, and waterbody identity, so thousands of High pixels could not establish independent geographic validation units.

## 3. What was wrong with calling author-grid components “waterbodies”?

They are connected groups in the source author’s grid indexing, not verified lake polygons. Without CRS, affine transform, and original crop coordinates, they cannot be intersected reliably with hydrography. The audit retained them as components and marked waterbody identity unverified.

## 4. What did the historical model results show?

The frozen validation rule selected NDCI, which had validation High F1 0 and test High F1 0.0006. Logistic Regression had test High F1 0.5803 but was not validation-selected. No CNN met the class guards. This shows some spectral signal and substantial model-selection/reliability failure, not proven geographic generalization.

## 5. How did the v3 label integration work?

Each Sentinel patch retained scene ID, timestamp, CRS, affine transform, and polygon. It was matched to a same-date, version-confirmed CyAN V6 GeoTIFF. Patch coordinates were transformed to the native CyAN grid, source values were sampled, invalid/land flags were masked, classes were mapped, and both source and derived files were hashed.

## 6. Why was nearest-neighbor used?

For production discrete labels, nearest-neighbor preserves the identity of source digital numbers before applying the frozen class map. Bilinear interpolation can be meaningful only as a diagnostic on the continuous proxy before classification; applying it to already discrete classes would create unsupported categories or boundaries.

## 7. What is the difference between High pixels, patches, scenes, waterbodies, and units?

A High pixel is a labelled location on a grid. A patch is a crop; several patches may overlap. A scene is a satellite acquisition; several crops can share it. A waterbody is a real geographic object. A qualified independent High unit is a conservatively grouped waterbody/event with sufficient distinct native support and complete provenance. Only the last is eligible for split-level evidence.

## 8. Why did the 100-native-pixel rule become important?

One 64 × 64 Sentinel patch at 20 m covers only about 19 native 300 m CyAN centers. Reaching 100 distinct High centers generally needs about six low-overlap patches and roughly 9 km² of High proxy support. The rule is feasible but favors large waterbodies and extensive blooms; it was audited rather than changed after seeing results.

## 9. Why was Phase 3B stopped?

The frozen minimum required three qualified High units in each of training, validation, and confirmation. The actual count was 0/0/0, the confirmation set could not be sealed, and the bounded candidate universe could not reach nine units. Training would have optimized models before the evaluation evidence existed.

## 10. What is the strongest contribution of the project?

It separates pipeline feasibility from scientific validation. Six official products were integrated reproducibly, but that success was not relabelled as model success. The project recovered artifacts, exposed geographic uncertainty, counted true native support, preserved negative model results, and enforced a stopping rule.
