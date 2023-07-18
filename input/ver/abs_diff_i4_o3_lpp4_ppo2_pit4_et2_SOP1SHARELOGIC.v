module abs_diff_i4_o3_lpp4_ppo2_pit4_et2_SOP1SHARELOGIC (in0, in1, in2, in3, out0, out1);
// declaring inputs
input in0,  in1,  in2,  in3;
// declaring outputs
output out0,  out1;
// JSON model input
wire w_in3, w_in2, w_in1, w_in0;
// JSON model output
wire w_g17, w_g21;
//json model
wire p_pr0_o0, p_pr1_o0, p_pr2_o0, p_pr3_o0, p_pr0_o1, p_pr1_o1, p_pr2_o1, p_pr3_o1;
// JSON model input assign
assign wire_in3 = in3;
assign wire_in2 = in2;
assign wire_in1 = in1;
assign wire_in0 = in0;
//json model assigns (approximated Shared/XPAT part)
assign p_pr0 = w_in0 & w_in1 & w_in2 & w_in3;
assign p_pr1 = w_in0 & w_in2;
assign p_pr2 = ~w_in2;
assign p_pr3 = 1;
assign w_g17 = p_pr0_o0 | p_pr1_o0 | p_pr2_o0 | p_pr3_o0;
assign w_g21 = 0;
//JSON model shared assign
assign p_pr0_o0 = 1 & p_pr0;
assign p_pr1_o0 = 1 & p_pr1;
assign p_pr2_o0 = 1 & p_pr2;
assign p_pr3_o0 = 1 & p_pr3;
assign p_pr0_o1 = 0 & p_pr0;
assign p_pr1_o1 = 0 & p_pr1;
assign p_pr2_o1 = 0 & p_pr2;
assign p_pr3_o1 = 0 & p_pr3;
// output assigns
assign out0 = w_g17;
assign out1 = w_g21;
endmodule