/////////////////////////////////////////////////////////////
// Created by: Synopsys DC Expert(TM) in wire load mode
// Version   : K-2015.06-SP5
// Date      : Tue Oct 12 16:52:24 2021
/////////////////////////////////////////////////////////////


module circ ( a, b, r );
  input [9:0] a;
  input [9:0] b;
  output [9:0] r;
  wire   n264, n265, n266, n267, n268, n269, n270, n271, n272, n273, n274,
         n275, n276, n277, n278, n279, n280, n281, n283, n284, n285, n286,
         n287, n288, n289, n290, n291, n292, n293, n294, n295, n296, n297,
         n298, n299, n300, n301, n302, n303, n304, n305, n306, n307, n308,
         n309, n310, n311, n312, n313, n314, n315, n316, n317, n318, n319,
         n320, n321, n322, n323, n324, n325, n326, n327, n328, n329, n330,
         n331, n332, n333, n334, n335, n336, n337, n338, n339, n340, n341,
         n342, n343, n344, n345, n346, n347, n348, n349, n350, n351, n352,
         n353, n354, n355, n356, n357, n358, n359, n360, n361, n362, n363,
         n364, n365, n366, n367, n368, n369, n370, n371, n372, n373, n374,
         n375, n376, n377, n378, n379, n380, n381, n382, n383, n384, n385,
         n386, n387, n388, n389, n390, n391, n392, n393, n394, n395, n396,
         n397, n398, n399, n400, n401, n402, n403, n404, n405, n406, n407,
         n408, n409, n410, n411, n412, n413, n414, n415, n416, n417, n418,
         n419, n420, n421, n422, n423, n424, n425, n426, n427, n428, n429,
         n430, n431, n432, n433, n434, n435, n436, n437, n438, n439, n440,
         n450;

assign n264 = ~a[9];
assign n265 = ~n307;
assign n266 = ~n336;
assign n267 = ~n349;
assign n268 = ~n332;
assign n269 = ~n350;
assign n270 = ~n328;
assign n271 = ~n351;
assign n272 = ~n324;
assign n273 = ~n352;
assign n274 = ~n320;
assign n275 = ~n353;
assign n276 = ~n316;
assign n277 = ~n354;
assign n278 = ~n314;
assign n279 = ~n313;
assign n280 = ~n356;
assign n281 = ~n308;
assign n283 = ~a[8];
assign n284 = ~a[7];
assign n285 = ~a[6];
assign n286 = ~a[5];
assign n287 = ~a[4];
assign n288 = ~a[3];
assign n289 = ~a[2];
assign n290 = ~a[1];
assign n291 = ~a[0];
assign n292 = ~b[9];
assign n293 = ~b[8];
assign n294 = ~b[7];
assign n295 = ~b[6];
assign n296 = ~b[5];
assign n297 = ~b[4];
assign n298 = ~b[3];
assign n299 = ~b[2];
assign n300 = ~b[1];
assign n301 = ~b[0];
assign r[9] = n302 & n303;
assign n303 = n304 | n305;
assign n305 = n306 & n292;
assign n304 = b[9] & n264;
assign n302 = n307 | n308;
assign r[0] = n309 | n310;
assign n310 = a[0] & n301;
assign n309 = b[0] & n291;
assign r[1] = n311 | n312;
assign n312 = n278 & n313;
assign n311 = n279 & n314;
assign r[2] = n315 & n276;
assign n315 = n317 | n318;
assign r[3] = n319 & n274;
assign n319 = n321 | n322;
assign r[4] = n323 & n272;
assign n323 = n325 | n326;
assign r[5] = n327 & n270;
assign n327 = n329 | n330;
assign r[6] = n331 & n268;
assign n331 = n333 | n334;
assign r[7] = n335 & n266;
assign n335 = n337 | n338;
assign r[8] = n339 & n265;
assign n307 = n340 & n341;
assign n339 = n341 | n340;
assign n340 = n342 | n343;
assign n343 = n344 & n281;
assign n308 = n344 & n345;
assign n345 = n293 | n283;
assign n344 = n346 | n347;
assign n347 = b[8] & n450;
assign n346 = a[8] & n348;
assign n342 = n283 & n293;
assign n341 = n336 | n349;
assign n336 = n338 & n337;
assign n337 = n332 | n350;
assign n332 = n334 & n333;
assign n333 = n328 | n351;
assign n328 = n330 & n329;
assign n329 = n324 | n352;
assign n324 = n326 & n325;
assign n325 = n320 | n353;
assign n320 = n322 & n321;
assign n321 = n316 | n354;
assign n316 = n318 & n317;
assign n317 = n355 | n356;
assign n355 = n314 & n313;
assign n313 = n357 | n358;
assign n358 = n359 & n280;
assign n356 = n359 & n360;
assign n360 = n290 | n300;
assign n359 = n361 | n362;
assign n362 = n450 & b[1];
assign n361 = a[1] & n348;
assign n357 = n290 & n300;
assign n314 = n363 | n364;
assign n364 = n365 | n366;
assign n366 = n450 & n291;
assign n365 = n348 & n301;
assign n363 = b[0] & a[0];
assign n318 = n367 | n368;
assign n368 = n369 & n277;
assign n354 = n369 & n370;
assign n370 = n289 | n299;
assign n369 = n371 | n372;
assign n372 = n450 & b[2];
assign n371 = a[2] & n348;
assign n367 = n289 & n299;
assign n322 = n373 | n374;
assign n374 = n375 & n275;
assign n353 = n375 & n376;
assign n376 = n288 | n298;
assign n375 = n377 | n378;
assign n378 = n450 & b[3];
assign n377 = a[3] & n348;
assign n373 = n288 & n298;
assign n326 = n379 | n380;
assign n380 = n381 & n273;
assign n352 = n381 & n382;
assign n382 = n287 | n297;
assign n381 = n383 | n384;
assign n384 = n450 & b[4];
assign n383 = a[4] & n348;
assign n379 = n287 & n297;
assign n330 = n385 | n386;
assign n386 = n387 & n271;
assign n351 = n387 & n388;
assign n388 = n296 | n286;
assign n387 = n389 | n390;
assign n390 = b[5] & n450;
assign n389 = a[5] & n348;
assign n385 = n286 & n296;
assign n334 = n391 | n392;
assign n392 = n393 & n269;
assign n350 = n393 & n394;
assign n394 = n295 | n285;
assign n393 = n395 | n396;
assign n396 = n450 & b[6];
assign n395 = a[6] & n348;
assign n391 = n285 & n295;
assign n338 = n397 | n398;
assign n398 = n399 & n267;
assign n349 = n399 & n400;
assign n400 = n284 | n294;
assign n399 = n401 | n402;
assign n402 = n450 & b[7];
assign n401 = a[7] & n348;
assign n348 = n306 | n403;
assign n403 = n292 & n404;
assign n306 = n405 & a[9];
assign n405 = n404 | n292;
assign n404 = n406 | n407;
assign n407 = a[8] & n408;
assign n406 = n409 & n293;
assign n409 = a[8] | n408;
assign n408 = n410 | n411;
assign n411 = n412 | n413;
assign n413 = a[7] & n294;
assign n412 = n414 & a[5];
assign n410 = n415 | n416;
assign n416 = n417 & n296;
assign n417 = n418 | n414;
assign n414 = n419 & n420;
assign n420 = n421 | n422;
assign n422 = a[4] & n297;
assign n421 = n423 & n424;
assign n424 = a[4] | n297;
assign n423 = n425 | n426;
assign n426 = n427 | n428;
assign n428 = n429 & a[2];
assign n429 = n430 & n299;
assign n427 = n431 & n432;
assign n432 = n433 | n434;
assign n434 = a[1] & n300;
assign n433 = n435 & a[0];
assign n435 = n436 & n301;
assign n436 = a[1] | n300;
assign n431 = n437 & n430;
assign n430 = a[3] | n298;
assign n437 = a[2] | n299;
assign n425 = a[3] & n298;
assign n418 = a[5] & n419;
assign n419 = n438 & n439;
assign n439 = n295 | a[6];
assign n415 = n440 & a[6];
assign n440 = n438 & n295;
assign n438 = a[7] | n294;
assign n397 = n284 & n294;
assign n450 = ~n348;
endmodule

