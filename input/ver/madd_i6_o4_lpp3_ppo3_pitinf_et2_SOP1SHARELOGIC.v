module madd_i6_o4_lpp3_ppo3_pitinf_et2_SOP1SHARELOGIC (in0, in1, in2, in3, in4, in5, out0, out1, out2, out3);
// declaring inputs
input in0,  in1,  in2,  in3,  in4,  in5;
// declaring outputs
output out0,  out1,  out2,  out3;
// JSON model input
wire w_in5, w_in4, w_in3, w_in2, w_in1, w_in0;
// JSON model output
wire w_g29, w_g46, w_g52, w_g54;
//json model
wire p_o0_t0, p_o0_t1, p_o0_t2, p_o1_t0, p_o1_t1, p_o1_t2, p_o2_t0, p_o2_t1, p_o2_t2, p_o3_t0, p_o3_t1, p_o3_t2;
// JSON model input assign
assign w_in5 = in5;
assign w_in4 = in4;
assign w_in3 = in3;
assign w_in2 = in2;
assign w_in1 = in1;
assign w_in0 = in0;
//json model assigns (approximated/XPATed part)
assign p_o0_t0 = ~w_in2 & w_in4;
assign p_o0_t1 = ~w_in0 & ~w_in1 & w_in3;
assign p_o0_t2 = w_in1 & w_in2 & ~w_in3;
assign out0 = p_o0_t0 | p_o0_t1 | p_o0_t2;
assign p_o1_t0 = ~w_in3 & ~w_in4 & w_in5;
assign p_o1_t1 = w_in1 & w_in3 & w_in5;
assign p_o1_t2 = ~w_in3 & w_in5;
assign out1 = p_o1_t0 | p_o1_t1 | p_o1_t2;
assign p_o2_t0 = w_in0 & w_in2 & w_in4;
assign p_o2_t1 = w_in1 & ~w_in2 & w_in3;
assign p_o2_t2 = w_in0 & ~w_in1 & w_in3;
assign out2 = p_o2_t0 | p_o2_t1 | p_o2_t2;
assign p_o3_t0 = w_in1 & w_in2 & w_in3;
assign p_o3_t1 = w_in1 & w_in2 & w_in3;
assign p_o3_t2 = w_in1 & w_in2 & w_in3;
assign out3 = p_o3_t0 | p_o3_t1 | p_o3_t2;
endmodule