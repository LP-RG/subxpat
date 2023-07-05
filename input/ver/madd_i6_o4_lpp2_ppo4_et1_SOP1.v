module madd_i6_o4_lpp2_ppo4_et1_SOP1 (in0, in1, in2, in3, in4, in5, out0, out1, out2, out3);
//input/output declarations
input in0, in1, in2, in3, in4, in5;
output out0, out1, out2, out3;
//intact gates wires 
wire w_g16, w_g17, w_g18, w_g19, w_g20, w_g21, w_g22, w_g23, w_g24, w_g25, w_g26, w_g27, w_g28, w_g29, w_g30, w_g31, w_g32, w_g33, w_g34, w_g35, w_g36, w_g37, w_g38, w_g39, w_g40, w_g41, w_g42, w_g43, w_g44, w_g45, w_g46, w_g47, w_g48, w_g49, w_g50, w_g51, w_g52, w_g53, w_g54;
//annotated subgraph inputs
wire w_in5, w_in4, w_in3, w_in2, w_in1, w_in0;
//annotated subgraph outputs
wire w_g6, w_g8, w_g10, w_g11, w_g12, w_g13, w_g14, w_g15;
// no json wires!
//json model
wire p_o0_t0, p_o0_t1, p_o0_t2, p_o0_t3, p_o1_t0, p_o1_t1, p_o1_t2, p_o1_t3, p_o2_t0, p_o2_t1, p_o2_t2, p_o2_t3, p_o3_t0, p_o3_t1, p_o3_t2, p_o3_t3, p_o4_t0, p_o4_t1, p_o4_t2, p_o4_t3, p_o5_t0, p_o5_t1, p_o5_t2, p_o5_t3, p_o6_t0, p_o6_t1, p_o6_t2, p_o6_t3, p_o7_t0, p_o7_t1, p_o7_t2, p_o7_t3;
//subgraph inputs assigns
assign w_in5 = in5;
assign w_in4 = in4;
assign w_in3 = in3;
assign w_in2 = in2;
assign w_in1 = in1;
assign w_in0 = in0;
//mapping subgraph inputs to json inputs
//json model assigns (approximated/XPATed part)
assign p_o0_t0 = ~w_in3 & ~w_in5;
assign p_o0_t1 = ~w_in1 & ~w_in5;
assign p_o0_t2 = ~w_in1 & ~w_in4;
assign p_o0_t3 = ~w_in2 & ~w_in3;
assign w_g6 = p_o0_t0 | p_o0_t1 | p_o0_t2 | p_o0_t3;
assign p_o1_t0 = ~w_in0 & w_in4;
assign p_o1_t1 = ~w_in0 & w_in4;
assign p_o1_t2 = ~w_in0 & w_in3;
assign p_o1_t3 = ~w_in3;
assign w_g8 = p_o1_t0 | p_o1_t1 | p_o1_t2 | p_o1_t3;
assign p_o2_t0 = ~w_in4 & ~w_in5;
assign p_o2_t1 = ~w_in2 & ~w_in5;
assign p_o2_t2 = w_in1 & ~w_in5;
assign p_o2_t3 = w_in1 & w_in3;
assign w_g10 = p_o2_t0 | p_o2_t1 | p_o2_t2 | p_o2_t3;
assign p_o3_t0 = ~w_in2 & ~w_in5;
assign p_o3_t1 = ~w_in2 & ~w_in5;
assign p_o3_t2 = ~w_in2 & ~w_in5;
assign p_o3_t3 = ~w_in0 & ~w_in4;
assign w_g11 = p_o3_t0 | p_o3_t1 | p_o3_t2 | p_o3_t3;
assign p_o4_t0 = w_in1 & w_in2;
assign p_o4_t1 = w_in4 & ~w_in5;
assign p_o4_t2 = w_in1 & w_in2;
assign p_o4_t3 = w_in1 & w_in2;
assign w_g12 = p_o4_t0 | p_o4_t1 | p_o4_t2 | p_o4_t3;
assign p_o5_t0 = w_in4 & w_in5;
assign p_o5_t1 = w_in1 & w_in3;
assign p_o5_t2 = ~w_in2 & w_in3;
assign p_o5_t3 = w_in2 & w_in5;
assign w_g13 = p_o5_t0 | p_o5_t1 | p_o5_t2 | p_o5_t3;
assign p_o6_t0 = w_in0 & ~w_in4;
assign p_o6_t1 = w_in0 & ~w_in2;
assign p_o6_t2 = ~w_in0 & w_in4;
assign p_o6_t3 = ~w_in2 & ~w_in5;
assign w_g14 = p_o6_t0 | p_o6_t1 | p_o6_t2 | p_o6_t3;
assign w_g15 = 0;
// intact gates assigns
assign w_g16 = ~w_g11;
assign w_g17 = w_in5 & w_g12;
assign w_g18 = ~w_g14;
assign w_g19 = w_in4 & w_g15;
assign w_g20 = ~w_g17;
assign w_g21 = ~w_g19;
assign w_g22 = w_g16 & w_g20;
assign w_g23 = w_g18 & w_g21;
assign w_g24 = ~w_g21;
assign w_g25 = ~w_g22;
assign w_g26 = ~w_g23;
assign w_g27 = w_g25 & w_g8;
assign w_g28 = ~w_g25;
assign w_g29 = ~w_g26;
assign w_g30 = ~w_g27;
assign w_g31 = w_g28 & w_g13;
assign w_g32 = ~w_g31;
assign w_g33 = w_g30 & w_g32;
assign w_g34 = w_g32 & w_g20;
assign w_g35 = ~w_g33;
assign w_g36 = ~w_g34;
assign w_g37 = w_g35 & w_g21;
assign w_g38 = ~w_g35;
assign w_g39 = w_g10 & w_g36;
assign w_g40 = ~w_g36;
assign w_g41 = ~w_g37;
assign w_g42 = w_g38 & w_g24;
assign w_g43 = ~w_g39;
assign w_g44 = w_g40 & w_g6;
assign w_g45 = ~w_g42;
assign w_g46 = ~w_g43;
assign w_g47 = ~w_g44;
assign w_g48 = w_g41 & w_g45;
assign w_g49 = w_g47 & w_g43;
assign w_g50 = ~w_g48;
assign w_g51 = ~w_g49;
assign w_g52 = ~w_g50;
assign w_g53 = w_g51 & w_g45;
assign w_g54 = ~w_g53;
// output assigns
assign out0 = w_g29;
assign out1 = w_g52;
assign out2 = w_g54;
assign out3 = w_g46;
endmodule