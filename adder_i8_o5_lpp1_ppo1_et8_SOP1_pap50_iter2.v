module adder_i8_o5_lpp1_ppo1_et8_SOP1_pap50_iter2 (in0, in1, in2, in3, in4, in5, in6, in7, out0, out1, out2, out3, out4);
//input/output declarations
input in0, in1, in2, in3, in4, in5, in6, in7;
output out0, out1, out2, out3, out4;
//intact gates wires 
wire w_g2;
//annotated subgraph inputs
wire w_in3, w_in2;
//annotated subgraph outputs
wire w_g1;
//json input wires
wire j_in0, j_in1;
//json model
wire p_o0_t0;
//subgraph inputs assigns
assign w_in3 = in3;
assign w_in2 = in2;
//mapping subgraph inputs to json inputs
assign j_in0 = w_in2;
assign j_in1 = w_in3;
//json model assigns (approximated/XPATed part)
assign p_o0_t0 = j_in1;
assign w_g1 = p_o0_t0;
// intact gates assigns
assign w_g2 = ~w_g1;
// output assigns
assign out0 = in4;
assign out1 = w_g2;
assign out2 = in6;
assign out3 = in7;
assign out4 = w_in3;
endmodule