module abs_diff_i8_o5_lpp2_ppo1_et6_SOP1_pap50_iter2 (in0, in1, in2, in3, in4, in5, in6, in7, out0, out1, out2, out3);
//input/output declarations
input in0, in1, in2, in3, in4, in5, in6, in7;
output out0, out1, out2, out3;
//intact gates wires 
wire w_g15, w_g16, w_g17, w_g18, w_g19, w_g20, w_g21, w_g22, w_g23, w_g24, w_g25, w_g26, w_g27, w_g28;
//annotated subgraph inputs
wire w_in7, w_in6, w_in5, w_in4, w_in3, w_in2;
//annotated subgraph outputs
wire w_g0, w_g2, w_g9, w_g10, w_g11, w_g12, w_g13, w_g14;
//json input wires
wire j_in0, j_in1, j_in2, j_in3, j_in4, j_in5;
//json model
wire p_o0_t0, p_o1_t0, p_o2_t0, p_o3_t0, p_o4_t0, p_o5_t0, p_o6_t0, p_o7_t0;
//subgraph inputs assigns
assign w_in7 = in7;
assign w_in6 = in6;
assign w_in5 = in5;
assign w_in4 = in4;
assign w_in3 = in3;
assign w_in2 = in2;
//mapping subgraph inputs to json inputs
assign j_in0 = w_in2;
assign j_in1 = w_in3;
assign j_in2 = w_in4;
assign j_in3 = w_in5;
assign j_in4 = w_in6;
assign j_in5 = w_in7;
//json model assigns (approximated/XPATed part)
assign p_o0_t0 = j_in1 & ~j_in5;
assign w_g0 = p_o0_t0;
assign p_o1_t0 = ~j_in0 & j_in4;
assign w_g2 = p_o1_t0;
assign p_o2_t0 = ~j_in1 & j_in4;
assign w_g9 = p_o2_t0;
assign p_o3_t0 = 1;
assign w_g10 = p_o3_t0;
assign p_o4_t0 = ~j_in0 & ~j_in4;
assign w_g11 = p_o4_t0;
assign p_o5_t0 = ~j_in0 & j_in1;
assign w_g12 = p_o5_t0;
assign p_o6_t0 = ~j_in1 & j_in5;
assign w_g13 = p_o6_t0;
assign w_g14 = 0;
// intact gates assigns
assign w_g15 = ~w_g9;
assign w_g16 = ~w_g10;
assign w_g17 = ~w_g12;
assign w_g18 = ~w_g15;
assign w_g19 = w_g2 & w_g11;
assign w_g20 = w_g0 & w_g17;
assign w_g21 = w_g13 & w_g18;
assign w_g22 = ~w_g19;
assign w_g23 = ~w_g20;
assign w_g24 = ~w_g21;
assign w_g25 = w_g22 & w_g16;
assign w_g26 = w_g23 & w_g24;
assign w_g27 = ~w_g25;
assign w_g28 = ~w_g26;
// output assigns
assign out0 = w_g14;
assign out1 = w_g27;
assign out2 = w_g11;
assign out3 = w_g28;
endmodule