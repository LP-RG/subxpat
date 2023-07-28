module adder_i8_o5_lpp1_ppo1_et12_SOP1_pap50_iter3 (in0, in1, in2, in3, in4, in5, in6, in7, out0, out1, out2, out3, out4);
//input/output declarations
input in0, in1, in2, in3, in4, in5, in6, in7;
output out0, out1, out2, out3, out4;
//intact gates wires 
wire w_g3, w_g4, w_g5;
//annotated subgraph inputs
wire w_in6, w_in2;
//annotated subgraph outputs
wire w_g1, w_g2;
//json input wires
wire j_in0, j_in1;
//json model
wire p_o0_t0, p_o1_t0;
//subgraph inputs assigns
assign w_in6 = in6;
assign w_in2 = in2;
//mapping subgraph inputs to json inputs
assign j_in0 = w_in2;
assign j_in1 = w_in6;
//json model assigns (approximated/XPATed part)
assign p_o0_t0 = ~j_in1;
assign w_g1 = p_o0_t0;
assign p_o1_t0 = ~j_in0;
assign w_g2 = p_o1_t0;
// intact gates assigns
assign w_g0 = 1'b0;
assign w_g3 = w_g1 & w_g2;
assign w_g4 = ~w_g3;
assign w_g5 = ~w_g4;
// output assigns
assign out0 = in4;
assign out1 = w_g0;
assign out2 = in7;
assign out3 = w_g5;
assign out4 = w_g4;
endmodule