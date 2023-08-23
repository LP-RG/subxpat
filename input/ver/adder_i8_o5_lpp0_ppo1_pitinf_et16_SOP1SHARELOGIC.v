module adder_i8_o5_lpp0_ppo1_pitinf_et16_SOP1SHARELOGIC (in0, in1, in2, in3, in4, in5, in6, in7, out0, out1, out2, out3, out4);
// declaring inputs
input in0,  in1,  in2,  in3,  in4,  in5,  in6,  in7;
// declaring outputs
output out0,  out1,  out2,  out3,  out4;
// JSON model input
wire w_in7, w_in6, w_in5, w_in4, w_in3, w_in2, w_in1, w_in0;
// JSON model output
wire w_g37, w_g45, w_g59, w_g62, w_g65;
//json model
wire p_o0_t0, p_o1_t0, p_o2_t0, p_o3_t0, p_o4_t0;
// JSON model input assign
assign w_in7 = in7;
assign w_in6 = in6;
assign w_in5 = in5;
assign w_in4 = in4;
assign w_in3 = in3;
assign w_in2 = in2;
assign w_in1 = in1;
assign w_in0 = in0;
//json model assigns (approximated/XPATed part)
assign out0 = 0;
assign out1 = 0;
assign out2 = 0;
assign out3 = 0;
assign p_o4_t0 = 1;
assign out4 = p_o4_t0;
endmodule