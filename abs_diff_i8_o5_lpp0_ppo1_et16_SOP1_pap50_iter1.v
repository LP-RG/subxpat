module abs_diff_i8_o5_lpp0_ppo1_et16_SOP1_pap50_iter1 (in0, in1, in2, in3, in4, in5, in6, in7, out0, out1, out2, out3);
//input/output declarations
input in0, in1, in2, in3, in4, in5, in6, in7;
output out0, out1, out2, out3;
//intact gates wires 
wire w_g54, w_g55, w_g56, w_g57, w_g58, w_g59, w_g60, w_g61, w_g62, w_g63, w_g64, w_g65, w_g66, w_g67, w_g68, w_g69, w_g70, w_g71, w_g72, w_g73, w_g74, w_g75, w_g76, w_g77, w_g78, w_g79, w_g80, w_g81, w_g82, w_g83, w_g84, w_g85, w_g86, w_g87, w_g88, w_g89, w_g90, w_g91, w_g92, w_g93, w_g94, w_g95, w_g96, w_g97, w_g98, w_g99, w_g100, w_g101, w_g102, w_g103, w_g104, w_g105;
//annotated subgraph inputs
wire w_in7, w_in6, w_in5, w_in4, w_in3, w_in2, w_in1, w_in0;
//annotated subgraph outputs
wire w_g16, w_g19, w_g20, w_g23, w_g26, w_g27, w_g31, w_g34, w_g35, w_g36, w_g40, w_g41, w_g43, w_g44, w_g47, w_g48, w_g51, w_g52, w_g53;
//json input wires
wire j_in0, j_in1, j_in2, j_in3, j_in4, j_in5, j_in6, j_in7;
//json model
wire p_o0_t0, p_o1_t0, p_o2_t0, p_o3_t0, p_o4_t0, p_o5_t0, p_o6_t0, p_o7_t0, p_o8_t0, p_o9_t0, p_o10_t0, p_o11_t0, p_o12_t0, p_o13_t0, p_o14_t0, p_o15_t0, p_o16_t0, p_o17_t0, p_o18_t0;
//subgraph inputs assigns
assign w_in7 = in7;
assign w_in6 = in6;
assign w_in5 = in5;
assign w_in4 = in4;
assign w_in3 = in3;
assign w_in2 = in2;
assign w_in1 = in1;
assign w_in0 = in0;
//mapping subgraph inputs to json inputs
assign j_in0 = w_in0;
assign j_in1 = w_in1;
assign j_in2 = w_in2;
assign j_in3 = w_in3;
assign j_in4 = w_in4;
assign j_in5 = w_in5;
assign j_in6 = w_in6;
assign j_in7 = w_in7;
//json model assigns (approximated/XPATed part)
assign w_g16 = 0;
assign w_g19 = 0;
assign p_o2_t0 = 1;
assign w_g20 = p_o2_t0;
assign w_g23 = 0;
assign p_o4_t0 = 1;
assign w_g26 = p_o4_t0;
assign w_g27 = 0;
assign p_o6_t0 = 1;
assign w_g31 = p_o6_t0;
assign p_o7_t0 = 1;
assign w_g34 = p_o7_t0;
assign w_g35 = 0;
assign p_o9_t0 = 1;
assign w_g36 = p_o9_t0;
assign p_o10_t0 = 1;
assign w_g40 = p_o10_t0;
assign w_g41 = 0;
assign p_o12_t0 = 1;
assign w_g43 = p_o12_t0;
assign p_o13_t0 = 1;
assign w_g44 = p_o13_t0;
assign p_o14_t0 = 1;
assign w_g47 = p_o14_t0;
assign w_g48 = 0;
assign w_g51 = 0;
assign w_g52 = 0;
assign p_o18_t0 = 1;
assign w_g53 = p_o18_t0;
// intact gates assigns
assign w_g54 = ~w_g52;
assign w_g55 = w_g43 & w_g53;
assign w_g56 = w_g27 & w_g54;
assign w_g57 = w_g54 & w_g16;
assign w_g58 = ~w_g54;
assign w_g59 = ~w_g55;
assign w_g60 = ~w_g56;
assign w_g61 = ~w_g57;
assign w_g62 = w_g58 & w_g20;
assign w_g63 = w_g59 & w_g60;
assign w_g64 = w_g61 & w_g20;
assign w_g65 = ~w_g62;
assign w_g66 = ~w_g63;
assign w_g67 = ~w_g64;
assign w_g68 = w_g65 & w_g16;
assign w_g69 = w_g67 & w_g44;
assign w_g70 = w_g47 & w_g67;
assign w_g71 = w_g67 & w_g19;
assign w_g72 = w_g26 & w_g67;
assign w_g73 = ~w_g68;
assign w_g74 = ~w_g69;
assign w_g75 = ~w_g70;
assign w_g76 = ~w_g71;
assign w_g77 = ~w_g72;
assign w_g78 = w_g51 & w_g73;
assign w_g79 = w_g48 & w_g73;
assign w_g80 = w_g73 & w_g23;
assign w_g81 = w_g31 & w_g73;
assign w_g82 = ~w_g78;
assign w_g83 = ~w_g79;
assign w_g84 = ~w_g80;
assign w_g85 = ~w_g81;
assign w_g86 = w_g82 & w_g74;
assign w_g87 = w_g83 & w_g75;
assign w_g88 = w_g76 & w_g84;
assign w_g89 = w_g85 & w_g77;
assign w_g90 = ~w_g86;
assign w_g91 = ~w_g87;
assign w_g92 = ~w_g88;
assign w_g93 = ~w_g89;
assign w_g94 = w_g90 & w_g34;
assign w_g95 = w_g40 & w_g91;
assign w_g96 = w_g92 & w_g35;
assign w_g97 = w_g41 & w_g93;
assign w_g98 = ~w_g94;
assign w_g99 = ~w_g95;
assign w_g100 = ~w_g96;
assign w_g101 = ~w_g97;
assign w_g102 = w_g98 & w_g99;
assign w_g103 = w_g101 & w_g100;
assign w_g104 = ~w_g102;
assign w_g105 = ~w_g103;
// output assigns
assign out0 = w_g36;
assign out1 = w_g105;
assign out2 = w_g104;
assign out3 = w_g66;
endmodule