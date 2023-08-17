module adder_i4_o3_lpp2_ppo2_pitinf_et1_SOP1SHARELOGIC (in0, in1, in2, in3, out0, out1, out2);
// declaring inputs
input in0,  in1,  in2,  in3;
// declaring outputs
output out0,  out1,  out2;
// JSON model input
wire w_in3, w_in2, w_in1, w_in0;
// JSON model output
wire w_g19, w_g26, w_g27;
//json model
wire p_o0_t0, p_o0_t1, p_o1_t0, p_o1_t1, p_o2_t0, p_o2_t1;
// JSON model input assign
assign w_in3 = in3;
assign w_in2 = in2;
assign w_in1 = in1;
assign w_in0 = in0;
//json model assigns (approximated/XPATed part)
assign p_o0_t0 = w_in1 & w_in2;
assign p_o0_t1 = ~w_in1 & w_in2;
assign out0 = p_o0_t0 | p_o0_t1;
assign p_o1_t0 = ~w_in1 & w_in3;
assign p_o1_t1 = w_in1 & ~w_in3;
assign out1 = p_o1_t0 | p_o1_t1;
assign p_o2_t0 = w_in1 & w_in3;
assign p_o2_t1 = w_in1 & w_in3;
assign out2 = p_o2_t0 | p_o2_t1;
endmodule