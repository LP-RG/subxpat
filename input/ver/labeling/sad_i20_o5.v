/////////////////////////////////////////////////////////////
// Created by: Synopsys DC Expert(TM) in wire load mode
// Version   : K-2015.06-SP5
// Date      : Wed Jan 26 18:36:43 2022
/////////////////////////////////////////////////////////////


module circ ( x0, x1, x2, x3, x4, r );
  input [3:0] x0;
  input [3:0] x1;
  input [3:0] x2;
  input [3:0] x3;
  input [3:0] x4;
  output [4:0] r;
  wire   n394, n395, n396, n397, n398, n399, n400, n401, n402, n403, n404,
         n405, n406, n407, n408, n409, n410, n411, n412, n413, n414, n415,
         n416, n417, n418, n419, n420, n421, n422, n423, n424, n425, n426,
         n427, n428, n429, n430, n431, n432, n433, n434, n435, n436, n437,
         n438, n439, n440, n441, n442, n443, n444, n445, n446, n447, n448,
         n449, n450, n451, n452, n453, n454, n455, n456, n457, n458, n459,
         n460, n461, n462, n463, n464, n465, n466, n467, n468, n469, n470,
         n471, n472, n473, n474, n475, n476, n477, n478, n479, n480, n481,
         n482, n483, n484, n485, n486, n487, n488, n489, n490, n491, n492,
         n493, n494, n495, n496, n497, n498, n499, n500, n501, n502, n503,
         n504, n505, n506, n507, n508, n509, n510, n511, n512, n513, n514,
         n515, n516, n517, n518, n519, n520, n521, n522, n523, n524, n525,
         n526, n527, n528, n529, n530, n531, n532, n533, n534, n535, n536,
         n537, n538, n539, n540, n541, n542, n543, n544, n545, n546, n547,
         n548, n549, n550, n551, n552, n553, n554, n555, n556, n557, n558,
         n559, n560, n561, n562, n563, n564, n565, n566, n567, n568, n569,
         n570, n571, n572, n573, n574, n575, n576, n577, n578, n579, n580,
         n581, n582, n583, n584, n585, n586, n587, n588, n589, n590, n591,
         n592, n593, n594, n595, n596, n597, n598, n599, n600, n601, n602,
         n603, n604, n605, n606, n607, n608, n609, n610, n611, n612, n613,
         n614, n615, n616, n617, n618, n619, n620, n621, n622, n623, n624,
         n625, n626, n627, n628, n629, n630, n631, n632, n633, n634, n635,
         n636, n637, n638, n639, n640, n641, n642, n643, n644, n645, n646,
         n647, n648, n649, n650, n651, n652, n653, n654, n655, n656, n657,
         n658, n659, n660, n661, n662, n663, n664, n665, n666, n667, n668,
         n669, n670, n671, n672, n673, n674, n675, n676, n677, n678, n679,
         n680, n681, n682, n683, n684, n685, n686, n687, n688, n689, n690,
         n691, n692, n693, n694, n695, n696, n697, n698, n699, n700, n701,
         n702, n703, n704, n705, n706, n707, n708, n709, n710, n711, n712,
         n713, n714, n715, n716, n717, n718, n719, n720, n721, n722, n723,
         n724, n725, n726, n727, n728, n729, n730, n731, n732, n733, n734,
         n735;

assign n394 = ~n501;
assign n395 = ~n481;
assign n396 = ~n484;
assign n397 = ~n506;
assign n398 = ~n494;
assign n399 = ~n509;
assign n400 = ~n511;
assign n401 = ~n497;
assign n402 = ~n508;
assign n403 = ~n553;
assign n404 = ~n485;
assign n405 = ~n649;
assign n406 = ~n503;
assign n407 = ~n493;
assign n408 = ~n583;
assign n409 = ~n502;
assign n410 = ~n491;
assign n411 = ~n620;
assign n412 = ~n624;
assign n413 = ~n671;
assign n414 = ~n623;
assign n415 = ~n627;
assign n416 = ~n630;
assign n417 = ~n660;
assign n418 = ~n685;
assign n419 = ~n588;
assign n420 = ~n572;
assign n421 = ~n489;
assign n422 = ~n689;
assign n423 = ~n692;
assign n424 = ~n621;
assign n425 = ~n638;
assign n426 = ~n641;
assign n427 = ~n606;
assign n428 = ~n709;
assign n429 = ~n592;
assign n430 = ~n595;
assign n431 = ~n598;
assign n432 = ~n686;
assign n433 = ~n720;
assign n434 = ~n573;
assign n435 = ~n609;
assign n436 = ~n612;
assign n437 = ~n556;
assign n438 = ~n540;
assign n439 = ~n527;
assign n440 = ~n514;
assign n441 = ~x0[3];
assign n442 = ~n559;
assign n443 = ~n543;
assign n444 = ~n530;
assign n445 = ~n517;
assign n446 = ~x0[2];
assign n447 = ~n519;
assign n448 = ~n524;
assign n449 = ~n532;
assign n450 = ~n537;
assign n451 = ~n545;
assign n452 = ~n550;
assign n453 = ~n561;
assign n454 = ~n566;
assign n455 = ~x0[1];
assign n456 = ~n581;
assign n457 = ~n616;
assign n458 = ~n655;
assign n459 = ~x0[0];
assign n460 = ~x1[3];
assign n461 = ~x1[2];
assign n462 = ~x1[1];
assign n463 = ~n657;
assign n464 = ~x1[0];
assign n465 = ~x2[3];
assign n466 = ~x2[2];
assign n467 = ~x2[1];
assign n468 = ~n658;
assign n469 = ~x2[0];
assign n470 = ~x3[3];
assign n471 = ~x3[2];
assign n472 = ~x3[1];
assign n473 = ~x3[0];
assign n474 = ~x4[3];
assign n475 = ~x4[2];
assign n476 = ~x4[1];
assign n477 = ~x4[0];
assign r[4] = n395 & n478;
assign n478 = n479 | n480;
assign n481 = n480 & n479;
assign n479 = n482 | n483;
assign n483 = n404 & n484;
assign n482 = n396 & n485;
assign n485 = n486 | n487;
assign n487 = n488 & n489;
assign n486 = n490 & n491;
assign n490 = n489 | n488;
assign n484 = n397 | n492;
assign n492 = n493 & n398;
assign n480 = n495 | n496;
assign n495 = n497 & n498;
assign r[3] = n394 & n499;
assign n499 = n407 | n500;
assign n501 = n500 & n407;
assign n493 = n502 | n503;
assign n500 = n397 | n494;
assign n494 = n504 & n505;
assign n506 = n504 | n505;
assign n505 = n507 | n496;
assign n496 = n508 & n399;
assign n507 = n402 & n509;
assign n509 = n510 & n400;
assign n511 = n401 & n498;
assign n510 = n498 | n401;
assign n497 = n512 | n513;
assign n513 = n514 & n515;
assign n515 = n516 | n517;
assign n516 = n447 & n518;
assign n512 = n520 & x0[3];
assign n520 = n521 & n465;
assign n521 = n522 | n523;
assign n522 = n518 & n524;
assign n498 = n525 | n526;
assign n526 = n527 & n528;
assign n528 = n529 | n530;
assign n529 = n449 & n531;
assign n525 = n533 & x0[3];
assign n533 = n534 & n470;
assign n534 = n535 | n536;
assign n535 = n531 & n537;
assign n508 = n538 | n539;
assign n539 = n540 & n541;
assign n541 = n542 | n543;
assign n542 = n451 & n544;
assign n538 = n546 & x0[3];
assign n546 = n547 & n460;
assign n547 = n548 | n549;
assign n548 = n544 & n550;
assign n504 = n403 | n551;
assign n551 = n552 & n488;
assign n553 = n552 | n488;
assign n488 = n554 | n555;
assign n555 = n556 & n557;
assign n557 = n558 | n559;
assign n558 = n453 & n560;
assign n554 = n562 & x0[3];
assign n562 = n563 & n474;
assign n563 = n564 | n565;
assign n564 = n560 & n566;
assign n552 = n567 | n568;
assign n568 = n421 & n491;
assign n567 = n410 & n489;
assign n489 = n569 | n570;
assign n570 = n429 & n434;
assign n569 = n571 & n572;
assign n571 = n429 | n434;
assign n491 = n574 | n575;
assign n575 = n411 & n424;
assign r[2] = n576 & n406;
assign n503 = n577 & n578;
assign n576 = n578 | n577;
assign n577 = n579 | n580;
assign n580 = n581 & n582;
assign n582 = n583 | n417;
assign n578 = n409 & n584;
assign n584 = n585 | n586;
assign n502 = n586 & n585;
assign n585 = n587 & n419;
assign n588 = n589 & n573;
assign n587 = n573 | n589;
assign n589 = n590 | n591;
assign n591 = n429 & n572;
assign n590 = n420 & n592;
assign n592 = n430 & n593;
assign n593 = n594 | n544;
assign n595 = n544 & n594;
assign n594 = n596 | n597;
assign n597 = n452 & n598;
assign n550 = n599 | n600;
assign n599 = n601 & n458;
assign n596 = n431 & n545;
assign n544 = n443 & n602;
assign n602 = n446 | x1[2];
assign n572 = n603 | n604;
assign n604 = n422 & n432;
assign n603 = n605 & n606;
assign n605 = n422 | n432;
assign n573 = n435 & n607;
assign n607 = n608 | n560;
assign n609 = n560 & n608;
assign n608 = n610 | n611;
assign n611 = n454 & n612;
assign n566 = n613 | n614;
assign n613 = n615 & n457;
assign n610 = n436 & n561;
assign n560 = n442 & n617;
assign n617 = n446 | x4[2];
assign n586 = n618 | n619;
assign n619 = n424 & n620;
assign n618 = n621 & n411;
assign n620 = n574 | n622;
assign n622 = n623 & n412;
assign n574 = n414 & n624;
assign n623 = n415 & n625;
assign n625 = n626 | n518;
assign n627 = n518 & n626;
assign n626 = n628 | n629;
assign n629 = n448 & n630;
assign n524 = n631 | n632;
assign n631 = n633 & n634;
assign n634 = x0[0] | n469;
assign n628 = n416 & n519;
assign n518 = n445 & n635;
assign n635 = n446 | x2[2];
assign n621 = n425 & n636;
assign n636 = n637 | n531;
assign n638 = n531 & n637;
assign n637 = n639 | n640;
assign n640 = n450 & n641;
assign n537 = n642 | n643;
assign n642 = n644 & n645;
assign n645 = x0[0] | n473;
assign n639 = n426 & n532;
assign n531 = n444 & n646;
assign n646 = n446 | x3[2];
assign r[1] = n405 & n647;
assign n647 = n456 | n648;
assign n649 = n648 & n456;
assign n581 = n650 | n651;
assign n651 = n652 & n653;
assign n653 = n616 | n654;
assign n652 = n655 | n656;
assign n650 = n657 & n658;
assign n648 = n579 | n659;
assign n659 = n660 & n408;
assign n579 = n417 & n583;
assign n583 = n661 & n412;
assign n624 = n662 & n663;
assign n661 = n663 | n662;
assign n662 = n664 & n665;
assign n665 = n666 | n667;
assign n666 = x2[0] & n459;
assign n664 = n668 | n669;
assign n668 = x3[0] & n459;
assign n663 = n670 | n413;
assign n671 = n672 | n633;
assign n670 = n633 & n672;
assign n672 = n673 | n674;
assign n674 = n416 & n667;
assign n673 = n675 & x2[0];
assign n675 = n630 & n459;
assign n630 = n676 | n677;
assign n677 = x0[3] & n465;
assign n676 = n678 & n440;
assign n514 = n441 & x2[3];
assign n678 = n679 | n523;
assign n523 = x0[2] & n466;
assign n679 = n519 & n445;
assign n517 = n446 & x2[2];
assign n519 = n680 | n632;
assign n632 = x0[1] & n467;
assign n680 = n667 & n681;
assign n667 = n469 & x0[0];
assign n633 = n681 & n682;
assign n682 = n455 | x2[1];
assign n681 = x0[1] | n467;
assign n660 = n683 | n684;
assign n684 = n685 & n686;
assign n683 = n432 & n418;
assign n685 = n687 | n688;
assign n688 = n422 & n606;
assign n687 = n427 & n689;
assign n689 = n423 & n690;
assign n690 = n691 | n644;
assign n692 = n644 & n691;
assign n691 = n693 | n694;
assign n694 = n426 & n669;
assign n693 = n695 & x3[0];
assign n695 = n641 & n459;
assign n641 = n696 | n697;
assign n697 = x0[3] & n470;
assign n696 = n698 & n439;
assign n527 = n441 & x3[3];
assign n698 = n699 | n536;
assign n536 = x0[2] & n471;
assign n699 = n532 & n444;
assign n530 = n446 & x3[2];
assign n532 = n700 | n643;
assign n643 = x0[1] & n472;
assign n700 = n669 & n701;
assign n669 = n473 & x0[0];
assign n644 = n701 & n702;
assign n702 = n455 | x3[1];
assign n701 = x0[1] | n472;
assign n606 = n703 | n704;
assign n704 = n705 & n601;
assign n705 = n706 & n707;
assign n707 = n656 | n598;
assign n706 = n655 | n431;
assign n703 = n428 & n708;
assign n708 = n431 | n458;
assign n655 = n459 & x1[0];
assign n709 = n710 | n601;
assign n601 = n711 & n712;
assign n712 = n455 | x1[1];
assign n710 = n656 & n431;
assign n598 = n713 | n714;
assign n714 = x0[3] & n460;
assign n713 = n715 & n438;
assign n540 = n441 & x1[3];
assign n715 = n716 | n549;
assign n549 = x0[2] & n461;
assign n716 = n545 & n443;
assign n543 = n446 & x1[2];
assign n545 = n717 | n600;
assign n600 = x0[1] & n462;
assign n717 = n656 & n711;
assign n711 = x0[1] | n462;
assign n656 = n464 & x0[0];
assign n686 = n433 & n718;
assign n718 = n719 | n615;
assign n720 = n615 & n719;
assign n719 = n721 | n722;
assign n722 = n616 & n612;
assign n616 = n459 & x4[0];
assign n721 = n436 & n654;
assign n612 = n723 | n724;
assign n724 = x0[3] & n474;
assign n723 = n725 & n437;
assign n556 = n441 & x4[3];
assign n725 = n726 | n565;
assign n565 = x0[2] & n475;
assign n726 = n561 & n442;
assign n559 = n446 & x4[2];
assign n561 = n727 | n614;
assign n614 = x0[1] & n476;
assign n727 = n654 & n728;
assign n654 = n477 & x0[0];
assign n615 = n728 & n729;
assign n729 = n455 | x4[1];
assign n728 = x0[1] | n476;
assign r[0] = n730 | n731;
assign n731 = n657 & n468;
assign n730 = n658 & n463;
assign n657 = n732 | n733;
assign n733 = x1[0] & n477;
assign n732 = x4[0] & n464;
assign n658 = n734 | n735;
assign n735 = x2[0] & n473;
assign n734 = x3[0] & n469;
endmodule

