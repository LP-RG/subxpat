module abs_diff_i4_o3_lpp0_ppo1_pitinf_et4_SOP1SHARELOGIC (in0, in1, in2, in3, out0, out1);
// declaring inputs
input in0,  in1,  in2,  in3;
// declaring outputs
output out0,  out1;
// JSON model input
wire w_in3, w_in2, w_in1, w_in0;
// JSON model output
wire w_g17, w_g21;
//json model
wire p_o0_t0, p_o1_t0;
// JSON model input assign
assign w_in3 = in3;
assign w_in2 = in2;
assign w_in1 = in1;
assign w_in0 = in0;
//json model assigns (approximated/XPATed part)
assign p_o0_t0 = 1;
assign out0 = p_o0_t0;
assign p_o1_t0 = 1;
assign out1 = p_o1_t0;
endmodule