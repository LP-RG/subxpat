module adder_i8_o5_lpp4_ppo4_et12_SOP1 (in0, in1, in2, in3, in4, in5, in6, in7, out0, out1, out2, out3, out4);
input in0, in1, in2, in3, in4, in5, in6, in7;
output out0, out1, out2, out3, out4;
//intact gates wires 
wire w_g15, w_g16, w_g17, w_g18, w_g19, w_g20, w_g21, w_g22, w_g23, w_g24, w_g25, w_g26, w_g27, w_g28, w_g29, w_g30, w_g31, w_g32, w_g33, w_g34, w_g35, w_g36, w_g37, w_g38, w_g39, w_g40, w_g41, w_g42, w_g43, w_g44, w_g45, w_g46, w_g47, w_g48, w_g49, w_g50, w_g51, w_g52, w_g53, w_g54, w_g55, w_g56, w_g57, w_g58;
//annotated subgraph inputs
wire w_in7, w_in6, w_in5, w_in4, w_in3, w_in2, w_in1, w_in0;
//annotated subgraph outputs
wire w_g1, w_g2, w_g3, w_g6, w_g7, w_g8, w_g9, w_g10, w_g11, w_g12, w_g13, w_g14;
//json model
wire p_o0_t0, p_o0_t1, p_o0_t2, p_o0_t3, p_o1_t0, p_o1_t1, p_o1_t2, p_o1_t3, p_o2_t0, p_o2_t1, p_o2_t2, p_o2_t3, p_o3_t0, p_o3_t1, p_o3_t2, p_o3_t3, p_o4_t0, p_o4_t1, p_o4_t2, p_o4_t3, p_o5_t0, p_o5_t1, p_o5_t2, p_o5_t3, p_o6_t0, p_o6_t1, p_o6_t2, p_o6_t3, p_o7_t0, p_o7_t1, p_o7_t2, p_o7_t3, p_o8_t0, p_o8_t1, p_o8_t2, p_o8_t3, p_o9_t0, p_o9_t1, p_o9_t2, p_o9_t3, p_o10_t0, p_o10_t1, p_o10_t2, p_o10_t3, p_o11_t0, p_o11_t1, p_o11_t2, p_o11_t3;
//subgraph inputs assigns
assign w_in7 = in7;
assign w_in6 = in6;
assign w_in5 = in5;
assign w_in4 = in4;
assign w_in3 = in3;
assign w_in2 = in2;
assign w_in1 = in1;
assign w_in0 = in0;
//json model assigns (approximated/XPATed part)
assign p_o0_t0 = w_in4 & w_in5 & w_in6 & w_in7;
assign p_o0_t1 = w_in0 & ~w_in3 & ~w_in4 & w_in7;
assign p_o0_t2 = w_in7;
assign p_o0_t3 = ~w_in5;
assign w_g1 = p_o0_t0 | p_o0_t1 | p_o0_t2 | p_o0_t3;
assign p_o1_t0 = ~w_in6 & ~w_in7;
assign p_o1_t1 = ~w_in0 & ~w_in5 & ~w_in7;
assign p_o1_t2 = ~w_in1 & ~w_in3 & ~w_in4 & ~w_in7;
assign p_o1_t3 = ~w_in3;
assign w_g2 = p_o1_t0 | p_o1_t1 | p_o1_t2 | p_o1_t3;
assign p_o2_t0 = w_in2 & ~w_in5 & ~w_in6;
assign p_o2_t1 = w_in2;
assign p_o2_t2 = w_in2;
assign p_o2_t3 = w_in2;
assign w_g3 = p_o2_t0 | p_o2_t1 | p_o2_t2 | p_o2_t3;
assign p_o3_t0 = ~w_in0 & ~w_in3 & ~w_in6 & w_in7;
assign p_o3_t1 = w_in3 & w_in4 & w_in5 & w_in7;
assign p_o3_t2 = ~w_in4 & ~w_in5 & ~w_in7;
assign p_o3_t3 = ~w_in0 & w_in2 & ~w_in3 & ~w_in6;
assign w_g6 = p_o3_t0 | p_o3_t1 | p_o3_t2 | p_o3_t3;
assign p_o4_t0 = w_in3 & w_in4 & w_in5 & w_in6;
assign p_o4_t1 = ~w_in4;
assign p_o4_t2 = ~w_in4;
assign p_o4_t3 = ~w_in0 & ~w_in1 & ~w_in2 & w_in3;
assign w_g7 = p_o4_t0 | p_o4_t1 | p_o4_t2 | p_o4_t3;
assign p_o5_t0 = ~w_in7;
assign p_o5_t1 = ~w_in7;
assign p_o5_t2 = w_in1 & ~w_in3 & ~w_in4 & w_in7;
assign p_o5_t3 = ~w_in7;
assign w_g8 = p_o5_t0 | p_o5_t1 | p_o5_t2 | p_o5_t3;
assign p_o6_t0 = ~w_in0 & ~w_in2 & w_in4 & w_in6;
assign p_o6_t1 = w_in1 & w_in2 & w_in3 & ~w_in7;
assign p_o6_t2 = w_in1 & w_in3 & w_in5 & ~w_in7;
assign p_o6_t3 = ~w_in6;
assign w_g9 = p_o6_t0 | p_o6_t1 | p_o6_t2 | p_o6_t3;
assign p_o7_t0 = w_in0 & ~w_in2 & w_in3 & w_in5;
assign p_o7_t1 = w_in0 & w_in1 & w_in3 & w_in5;
assign p_o7_t2 = w_in0 & ~w_in2 & w_in3 & w_in5;
assign p_o7_t3 = ~w_in1 & w_in2 & ~w_in3 & ~w_in7;
assign w_g10 = p_o7_t0 | p_o7_t1 | p_o7_t2 | p_o7_t3;
assign p_o8_t0 = w_in4 & w_in5 & ~w_in6 & w_in7;
assign p_o8_t1 = ~w_in2 & w_in3 & w_in5 & ~w_in7;
assign p_o8_t2 = ~w_in2 & ~w_in4 & w_in5 & ~w_in7;
assign p_o8_t3 = ~w_in0 & ~w_in1 & w_in5 & ~w_in6;
assign w_g11 = p_o8_t0 | p_o8_t1 | p_o8_t2 | p_o8_t3;
assign p_o9_t0 = w_in1 & w_in2 & w_in4 & w_in5;
assign p_o9_t1 = w_in2 & w_in4 & w_in5 & w_in6;
assign p_o9_t2 = w_in1 & w_in2 & w_in5 & ~w_in7;
assign p_o9_t3 = w_in2 & w_in4 & w_in5 & ~w_in7;
assign w_g12 = p_o9_t0 | p_o9_t1 | p_o9_t2 | p_o9_t3;
assign p_o10_t0 = ~w_in2 & ~w_in4 & ~w_in5 & ~w_in6;
assign p_o10_t1 = ~w_in0 & ~w_in1 & ~w_in3 & ~w_in7;
assign p_o10_t2 = w_in0 & w_in1 & ~w_in2 & w_in7;
assign p_o10_t3 = w_in0 & ~w_in3 & ~w_in4 & w_in5;
assign w_g13 = p_o10_t0 | p_o10_t1 | p_o10_t2 | p_o10_t3;
assign p_o11_t0 = ~w_in0 & ~w_in1 & ~w_in2 & ~w_in3 & ~w_in4 & ~w_in5 & ~w_in6 & ~w_in7;
assign p_o11_t1 = ~w_in0 & ~w_in1 & ~w_in2 & w_in3 & w_in4 & w_in5 & ~w_in6 & w_in7;
assign p_o11_t2 = 1;
assign p_o11_t3 = 1;
assign w_g14 = p_o11_t0 | p_o11_t1 | p_o11_t2 | p_o11_t3;
// intact gates assigns
assign w_g15 = ~w_g6;
assign w_g16 = ~w_g6;
assign w_g17 = w_g1 & w_g7;
assign w_g18 = ~w_g8;
assign w_g19 = ~w_g8;
assign w_g20 = w_g2 & w_g9;
assign w_g21 = ~w_g10;
assign w_g22 = ~w_g10;
assign w_g23 = w_g3 & w_g11;
assign w_g24 = ~w_g14;
assign w_g25 = ~w_g17;
assign w_g26 = ~w_g20;
assign w_g27 = ~w_g23;
assign w_g28 = w_g24 & w_g13;
assign w_g29 = w_g25 & w_g16;
assign w_g30 = w_g26 & w_g19;
assign w_g31 = w_g27 & w_g22;
assign w_g32 = ~w_g28;
assign w_g33 = ~w_g29;
assign w_g34 = ~w_g30;
assign w_g35 = w_g10 & w_g30;
assign w_g36 = w_g34 & w_g21;
assign w_g37 = ~w_g35;
assign w_g38 = ~w_g35;
assign w_g39 = ~w_g36;
assign w_g40 = w_g37 & w_g18;
assign w_g41 = w_g39 & w_g38;
assign w_g42 = w_g33 & w_g40;
assign w_g43 = ~w_g40;
assign w_g44 = ~w_g42;
assign w_g45 = w_g43 & w_g29;
assign w_g46 = ~w_g45;
assign w_g47 = ~w_g45;
assign w_g48 = w_g46 & w_g15;
assign w_g49 = w_g44 & w_g47;
assign w_g50 = w_g32 & w_g48;
assign w_g51 = ~w_g48;
assign w_g52 = ~w_g50;
assign w_g53 = w_g51 & w_g28;
assign w_g54 = ~w_g53;
assign w_g55 = ~w_g53;
assign w_g56 = w_g54 & w_g12;
assign w_g57 = w_g52 & w_g55;
assign w_g58 = ~w_g56;
// output assigns
assign out0 = w_g31;
assign out1 = w_g41;
assign out2 = w_g49;
assign out3 = w_g57;
assign out4 = w_g58;
endmodule