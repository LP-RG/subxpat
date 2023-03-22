// Benchmark "circuit" written by ABC on Sun Jul  8 15:05:00 2018

module circuit ( 
    g0, g1, g2, g3, g4, g5, g6, g7, g8, g9, g10, g11, g12, g13, g14, g15,
    g16, g17, g18, g19, g20, g21, g22, g23, g24, g25, g26, g27, g28, g29,
    g30, g31,
    g251, g250, g249, g248, g247, g246, g245, g244, g243, g242, g241, g240,
    g239, g238, g237, g236, g235  );
  input  g0, g1, g2, g3, g4, g5, g6, g7, g8, g9, g10, g11, g12, g13, g14,
    g15, g16, g17, g18, g19, g20, g21, g22, g23, g24, g25, g26, g27, g28,
    g29, g30, g31;
  output g251, g250, g249, g248, g247, g246, g245, g244, g243, g242, g241,
    g240, g239, g238, g237, g236, g235;
  wire g32, g33, g34, g35, g36, g37, g38, g39, g40, g41, g42, g43, g44, g45,
    g46, g47, g48, g49, g50, g51, g52, g53, g54, g55, g56, g57, g58, g59,
    g60, g61, g62, g63, g64, g65, g66, g67, g68, g69, g70, g71, g72, g73,
    g74, g75, g76, g77, g78, g79, g80, g81, g82, g83, g84, g85, g86, g87,
    g88, g89, g90, g91, g92, g93, g94, g95, g96, g97, g98, g99, g100, g101,
    g102, g103, g104, g105, g106, g107, g108, g109, g110, g111, g112, g113,
    g114, g115, g116, g117, g118, g119, g120, g121, g122, g123, g124, g125,
    g126, g127, g128, g129, g130, g131, g132, g133, g134, g135, g136, g137,
    g138, g139, g140, g141, g142, g143, g144, g145, g146, g147, g148, g149,
    g150, g151, g152, g153, g154, g155, g156, g157, g158, g159, g160, g161,
    g162, g163, g164, g165, g166, g167, g168, g169, g170, g171, g172, g173,
    g174, g175, g176, g177, g178, g179, g180, g181, g182, g183, g184, g185,
    g186, g187, g188, g189, g190, g191, g192, g193, g194, g195, g196, g197,
    g198, g199, g200, g201, g202, g203, g204, g205, g206, g207, g208, g209,
    g210, g211, g212, g213, g214, g215, g216, g217, g218, g219, g220, g221,
    g222, g223, g224, g225, g226, g227, g228, g229, g230, g231, g232, g233,
    g234;
  assign g32 = ~g31;
  assign g33 = ~g15 | ~g32;
  assign g34 = ~g15;
  assign g35 = ~g31 | ~g34;
  assign g36 = ~g21;
  assign g37 = ~g5 | ~g36;
  assign g38 = ~g5;
  assign g39 = ~g21 | ~g38;
  assign g40 = ~g37 | ~g39;
  assign g41 = ~g6;
  assign g42 = ~g22;
  assign g43 = ~g41 | ~g42;
  assign g44 = ~g7;
  assign g45 = ~g23;
  assign g46 = ~g44 | ~g45;
  assign g47 = ~g8;
  assign g48 = ~g24;
  assign g49 = ~g47 | ~g48;
  assign g50 = ~g9;
  assign g51 = ~g25;
  assign g52 = ~g50 | ~g51;
  assign g53 = ~g10;
  assign g54 = ~g26;
  assign g55 = ~g53 | ~g54;
  assign g56 = ~g11;
  assign g57 = ~g27;
  assign g58 = ~g56 | ~g57;
  assign g59 = ~g12;
  assign g60 = ~g28;
  assign g61 = ~g59 | ~g60;
  assign g62 = ~g13;
  assign g63 = ~g29;
  assign g64 = ~g62 | ~g63;
  assign g65 = ~g14 | ~g15;
  assign g66 = ~g32 & ~g65;
  assign g67 = ~g30;
  assign g68 = ~g15 | ~g31;
  assign g69 = ~g67 & ~g68;
  assign g70 = ~g66 & ~g69;
  assign g71 = ~g14 | ~g30;
  assign g72 = ~g70 | ~g71;
  assign g73 = ~g64 | ~g72;
  assign g74 = ~g13 | ~g29;
  assign g75 = ~g73 | ~g74;
  assign g76 = ~g61 | ~g75;
  assign g77 = ~g12 | ~g28;
  assign g78 = ~g76 | ~g77;
  assign g79 = ~g58 | ~g78;
  assign g80 = ~g11 | ~g27;
  assign g81 = ~g79 | ~g80;
  assign g82 = ~g55 | ~g81;
  assign g83 = ~g10 | ~g26;
  assign g84 = ~g82 | ~g83;
  assign g85 = ~g52 | ~g84;
  assign g86 = ~g9 | ~g25;
  assign g87 = ~g85 | ~g86;
  assign g88 = ~g49 | ~g87;
  assign g89 = ~g8 | ~g24;
  assign g90 = ~g88 | ~g89;
  assign g91 = ~g46 | ~g90;
  assign g92 = ~g7 | ~g23;
  assign g93 = ~g91 | ~g92;
  assign g94 = ~g43 | ~g93;
  assign g95 = ~g6 | ~g22;
  assign g96 = ~g94 | ~g95;
  assign g97 = ~g40 | ~g96;
  assign g98 = ~g97;
  assign g99 = ~g40 & ~g96;
  assign g100 = ~g20;
  assign g101 = ~g4 | ~g100;
  assign g102 = ~g4;
  assign g103 = ~g20 | ~g102;
  assign g104 = ~g101 | ~g103;
  assign g105 = ~g36 | ~g38;
  assign g106 = ~g96 | ~g105;
  assign g107 = ~g5 | ~g21;
  assign g108 = ~g106 | ~g107;
  assign g109 = ~g104 | ~g108;
  assign g110 = ~g109;
  assign g111 = ~g104 & ~g108;
  assign g112 = ~g19;
  assign g113 = ~g3 | ~g112;
  assign g114 = ~g3;
  assign g115 = ~g19 | ~g114;
  assign g116 = ~g113 | ~g115;
  assign g117 = ~g100 | ~g102;
  assign g118 = ~g108 | ~g117;
  assign g119 = ~g4 | ~g20;
  assign g120 = ~g118 | ~g119;
  assign g121 = ~g116 | ~g120;
  assign g122 = ~g121;
  assign g123 = ~g116 & ~g120;
  assign g124 = ~g18;
  assign g125 = ~g2 | ~g124;
  assign g126 = ~g2;
  assign g127 = ~g18 | ~g126;
  assign g128 = ~g125 | ~g127;
  assign g129 = ~g112 | ~g114;
  assign g130 = ~g120 | ~g129;
  assign g131 = ~g3 | ~g19;
  assign g132 = ~g130 | ~g131;
  assign g133 = ~g128 | ~g132;
  assign g134 = ~g133;
  assign g135 = ~g128 & ~g132;
  assign g136 = ~g17;
  assign g137 = ~g1 | ~g136;
  assign g138 = ~g1;
  assign g139 = ~g17 | ~g138;
  assign g140 = ~g137 | ~g139;
  assign g141 = ~g124 | ~g126;
  assign g142 = ~g132 | ~g141;
  assign g143 = ~g2 | ~g18;
  assign g144 = ~g142 | ~g143;
  assign g145 = ~g140 | ~g144;
  assign g146 = ~g145;
  assign g147 = ~g140 & ~g144;
  assign g148 = ~g16;
  assign g149 = ~g0 | ~g148;
  assign g150 = ~g0;
  assign g151 = ~g16 | ~g150;
  assign g152 = ~g149 | ~g151;
  assign g153 = ~g136 | ~g138;
  assign g154 = ~g144 | ~g153;
  assign g155 = ~g1 | ~g17;
  assign g156 = ~g154 | ~g155;
  assign g157 = ~g152 | ~g156;
  assign g158 = ~g157;
  assign g159 = ~g152 & ~g156;
  assign g160 = ~g148 | ~g150;
  assign g161 = ~g156 | ~g160;
  assign g162 = ~g0 | ~g16;
  assign g163 = ~g14 | ~g67;
  assign g164 = ~g14;
  assign g165 = ~g30 | ~g164;
  assign g166 = ~g163 | ~g165;
  assign g167 = ~g68 | ~g166;
  assign g168 = ~g68 & ~g166;
  assign g169 = ~g168;
  assign g170 = ~g13 | ~g63;
  assign g171 = ~g29 | ~g62;
  assign g172 = ~g170 | ~g171;
  assign g173 = ~g72 | ~g172;
  assign g174 = ~g173;
  assign g175 = ~g72 & ~g172;
  assign g176 = ~g12 | ~g60;
  assign g177 = ~g28 | ~g59;
  assign g178 = ~g176 | ~g177;
  assign g179 = ~g75 | ~g178;
  assign g180 = ~g179;
  assign g181 = ~g75 & ~g178;
  assign g182 = ~g11 | ~g57;
  assign g183 = ~g27 | ~g56;
  assign g184 = ~g182 | ~g183;
  assign g185 = ~g78 | ~g184;
  assign g186 = ~g185;
  assign g187 = ~g78 & ~g184;
  assign g188 = ~g10 | ~g54;
  assign g189 = ~g26 | ~g53;
  assign g190 = ~g188 | ~g189;
  assign g191 = ~g81 | ~g190;
  assign g192 = ~g191;
  assign g193 = ~g81 & ~g190;
  assign g194 = ~g9 | ~g51;
  assign g195 = ~g25 | ~g50;
  assign g196 = ~g194 | ~g195;
  assign g197 = ~g84 | ~g196;
  assign g198 = ~g197;
  assign g199 = ~g84 & ~g196;
  assign g200 = ~g8 | ~g48;
  assign g201 = ~g24 | ~g47;
  assign g202 = ~g200 | ~g201;
  assign g203 = ~g87 | ~g202;
  assign g204 = ~g203;
  assign g205 = ~g87 & ~g202;
  assign g206 = ~g7 | ~g45;
  assign g207 = ~g23 | ~g44;
  assign g208 = ~g206 | ~g207;
  assign g209 = ~g90 | ~g208;
  assign g210 = ~g209;
  assign g211 = ~g90 & ~g208;
  assign g212 = ~g6 | ~g42;
  assign g213 = ~g22 | ~g41;
  assign g214 = ~g212 | ~g213;
  assign g215 = ~g93 | ~g214;
  assign g216 = ~g215;
  assign g217 = ~g93 & ~g214;
  assign g218 = ~g33 | ~g35;
  assign g219 = ~g167 | ~g169;
  assign g220 = ~g174 & ~g175;
  assign g221 = ~g180 & ~g181;
  assign g222 = ~g186 & ~g187;
  assign g223 = ~g192 & ~g193;
  assign g224 = ~g198 & ~g199;
  assign g225 = ~g204 & ~g205;
  assign g226 = ~g210 & ~g211;
  assign g227 = ~g216 & ~g217;
  assign g228 = ~g98 & ~g99;
  assign g229 = ~g110 & ~g111;
  assign g230 = ~g122 & ~g123;
  assign g231 = ~g134 & ~g135;
  assign g232 = ~g146 & ~g147;
  assign g233 = ~g158 & ~g159;
  assign g234 = ~g161 | ~g162;
  assign g235 = g218;
  assign g236 = g219;
  assign g237 = g220;
  assign g238 = g221;
  assign g239 = g222;
  assign g240 = g223;
  assign g241 = g224;
  assign g242 = g225;
  assign g243 = g226;
  assign g244 = g227;
  assign g245 = g228;
  assign g246 = g229;
  assign g247 = g230;
  assign g248 = g231;
  assign g249 = g232;
  assign g250 = g233;
  assign g251 = g234;
endmodule


