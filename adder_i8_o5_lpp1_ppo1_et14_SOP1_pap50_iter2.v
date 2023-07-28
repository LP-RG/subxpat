module adder_i8_o5_lpp1_ppo1_et14_SOP1_pap50_iter2 (in0, in1, in2, in3, in4, in5, in6, in7, out0, out1, out2, out3, out4);
//input/output declarations
input in0, in1, in2, in3, in4, in5, in6, in7;
output out0, out1, out2, out3, out4;
//intact gates wires 
wire w_g4, w_g5, w_g6, w_g7;
//annotated subgraph inputs
wire w_in7, w_in6;
//annotated subgraph outputs
wire w_g1, w_g3;
//json input wires
wire j_in0, j_in1;
//json model
wire p_o0_t0, p_o1_t0;
//subgraph inputs assigns
assign w_in7 = in7;
assign w_in6 = in6;
//mapping subgraph inputs to json inputs
assign j_in0 = w_in6;
assign j_in1 = w_in7;
//json model assigns (approximated/XPATed part)
assign p_o0_t0 = ~j_in1;
assign w_g1 = p_o0_t0;
assign p_o1_t0 = ~j_in1;
assign w_g3 = p_o1_t0;
// intact gates assigns
assign w_g0 = 1'b1;
assign w_g4 = ~w_g3;
assign w_g5 = in3 & w_g4;
assign w_g6 = ~w_g5;
assign w_g7 = ~w_g6;
// output assigns
assign out0 = w_g0;
assign out1 = w_g4;
assign out2 = w_g7;
assign out3 = w_g1;
assign out4 = w_in7;
endmodule