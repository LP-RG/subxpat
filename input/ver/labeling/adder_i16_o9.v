// Benchmark "circuit" written by ABC on Wed Mar 16 10:20:12 2022

module circuit ( 
    g0, g1, g2, g3, g4, g5, g6, g7, g8, g9, g10, g11, g12, g13, g14, g15,
    g123, g122, g121, g120, g119, g118, g117, g116, g115  );
  input  g0, g1, g2, g3, g4, g5, g6, g7, g8, g9, g10, g11, g12, g13, g14,
    g15;
  output g123, g122, g121, g120, g119, g118, g117, g116, g115;
  wire g16, g17, g18, g19, g20, g21, g22, g23, g24, g25, g26, g27, g28, g29,
    g30, g31, g32, g33, g34, g35, g36, g37, g38, g39, g40, g41, g42, g43,
    g44, g45, g46, g47, g48, g49, g50, g51, g52, g53, g54, g55, g56, g57,
    g58, g59, g60, g61, g62, g63, g64, g65, g66, g67, g68, g69, g70, g71,
    g72, g73, g74, g75, g76, g77, g78, g79, g80, g81, g82, g83, g84, g85,
    g86, g87, g88, g89, g90, g91, g92, g93, g94, g95, g96, g97, g98, g99,
    g100, g101, g102, g103, g104, g105, g106, g107, g108, g109, g110, g111,
    g112, g113, g114;
  assign g16 = ~g15;
  assign g17 = ~g7 | ~g16;
  assign g18 = ~g7;
  assign g19 = ~g15 | ~g18;
  assign g20 = ~g14;
  assign g21 = ~g6 | ~g20;
  assign g22 = ~g6;
  assign g23 = ~g14 | ~g22;
  assign g24 = ~g21 | ~g23;
  assign g25 = ~g7 | ~g15;
  assign g26 = ~g24 | ~g25;
  assign g27 = ~g24 & ~g25;
  assign g28 = ~g27;
  assign g29 = ~g13;
  assign g30 = ~g5 | ~g29;
  assign g31 = ~g5;
  assign g32 = ~g13 | ~g31;
  assign g33 = ~g30 | ~g32;
  assign g34 = ~g6 | ~g7;
  assign g35 = ~g16 & ~g34;
  assign g36 = ~g20 & ~g25;
  assign g37 = ~g35 & ~g36;
  assign g38 = ~g6 | ~g14;
  assign g39 = ~g37 | ~g38;
  assign g40 = ~g33 | ~g39;
  assign g41 = ~g40;
  assign g42 = ~g33 & ~g39;
  assign g43 = ~g12;
  assign g44 = ~g4 | ~g43;
  assign g45 = ~g4;
  assign g46 = ~g12 | ~g45;
  assign g47 = ~g44 | ~g46;
  assign g48 = ~g29 | ~g31;
  assign g49 = ~g39 | ~g48;
  assign g50 = ~g5 | ~g13;
  assign g51 = ~g49 | ~g50;
  assign g52 = ~g47 | ~g51;
  assign g53 = ~g52;
  assign g54 = ~g47 & ~g51;
  assign g55 = ~g11;
  assign g56 = ~g3 | ~g55;
  assign g57 = ~g3;
  assign g58 = ~g11 | ~g57;
  assign g59 = ~g56 | ~g58;
  assign g60 = ~g43 | ~g45;
  assign g61 = ~g51 | ~g60;
  assign g62 = ~g4 | ~g12;
  assign g63 = ~g61 | ~g62;
  assign g64 = ~g59 | ~g63;
  assign g65 = ~g64;
  assign g66 = ~g59 & ~g63;
  assign g67 = ~g10;
  assign g68 = ~g2 | ~g67;
  assign g69 = ~g2;
  assign g70 = ~g10 | ~g69;
  assign g71 = ~g68 | ~g70;
  assign g72 = ~g55 | ~g57;
  assign g73 = ~g63 | ~g72;
  assign g74 = ~g3 | ~g11;
  assign g75 = ~g73 | ~g74;
  assign g76 = ~g71 | ~g75;
  assign g77 = ~g76;
  assign g78 = ~g71 & ~g75;
  assign g79 = ~g9;
  assign g80 = ~g1 | ~g79;
  assign g81 = ~g1;
  assign g82 = ~g9 | ~g81;
  assign g83 = ~g80 | ~g82;
  assign g84 = ~g67 | ~g69;
  assign g85 = ~g75 | ~g84;
  assign g86 = ~g2 | ~g10;
  assign g87 = ~g85 | ~g86;
  assign g88 = ~g83 | ~g87;
  assign g89 = ~g88;
  assign g90 = ~g83 & ~g87;
  assign g91 = ~g8;
  assign g92 = ~g0 | ~g91;
  assign g93 = ~g0;
  assign g94 = ~g8 | ~g93;
  assign g95 = ~g92 | ~g94;
  assign g96 = ~g79 | ~g81;
  assign g97 = ~g87 | ~g96;
  assign g98 = ~g1 | ~g9;
  assign g99 = ~g97 | ~g98;
  assign g100 = ~g95 | ~g99;
  assign g101 = ~g100;
  assign g102 = ~g95 & ~g99;
  assign g103 = ~g91 | ~g93;
  assign g104 = ~g99 | ~g103;
  assign g105 = ~g0 | ~g8;
  assign g106 = ~g17 | ~g19;
  assign g107 = ~g26 | ~g28;
  assign g108 = ~g41 & ~g42;
  assign g109 = ~g53 & ~g54;
  assign g110 = ~g65 & ~g66;
  assign g111 = ~g77 & ~g78;
  assign g112 = ~g89 & ~g90;
  assign g113 = ~g101 & ~g102;
  assign g114 = ~g104 | ~g105;
  assign g115 = g106;
  assign g116 = g107;
  assign g117 = g108;
  assign g118 = g109;
  assign g119 = g110;
  assign g120 = g111;
  assign g121 = g112;
  assign g122 = g113;
  assign g123 = g114;
endmodule


