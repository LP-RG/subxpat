module adder_i8_o5_lpp1_ppo1_et10_SOP1_pap50_iter2 (in0, in1, in2, in3, in4, in5, in6, in7, out0, out1, out2, out3, out4);
//input/output declarations
input in0, in1, in2, in3, in4, in5, in6, in7;
output out0, out1, out2, out3, out4;
//intact gates wires 
wire w_g12, w_g13, w_g14, w_g15, w_g16, w_g17, w_g18, w_g19, w_g20, w_g21, w_g22;
//annotated subgraph inputs
wire w_in6, w_in5, w_in3, w_in1;
//annotated subgraph outputs
wire w_g1, w_g4, w_g10, w_g11;
//json input wires
wire j_in0, j_in1, j_in2, j_in3;
//json model
wire p_o0_t0, p_o1_t0, p_o2_t0, p_o3_t0;
//subgraph inputs assigns
assign w_in6 = in6;
assign w_in5 = in5;
assign w_in3 = in3;
assign w_in1 = in1;
//mapping subgraph inputs to json inputs
assign j_in0 = w_in1;
assign j_in1 = w_in3;
assign j_in2 = w_in5;
assign j_in3 = w_in6;
//json model assigns (approximated/XPATed part)
assign p_o0_t0 = j_in2;
assign w_g1 = p_o0_t0;
assign p_o1_t0 = j_in2;
assign w_g4 = p_o1_t0;
assign p_o2_t0 = j_in3;
assign w_g10 = p_o2_t0;
assign p_o3_t0 = 1;
assign w_g11 = p_o3_t0;
// intact gates assigns
assign w_g0 = 1'b1;
assign w_g12 = ~w_g10;
assign w_g13 = in7 & w_g11;
assign w_g14 = ~w_g11;
assign w_g15 = ~w_g12;
assign w_g16 = ~w_g13;
assign w_g17 = w_g1 & w_g14;
assign w_g18 = ~w_g16;
assign w_g19 = ~w_g17;
assign w_g20 = w_g19 & w_g16;
assign w_g21 = ~w_g20;
assign w_g22 = ~w_g21;
// output assigns
assign out0 = w_g4;
assign out1 = w_g0;
assign out2 = w_g15;
assign out3 = w_g22;
assign out4 = w_g18;
endmodule