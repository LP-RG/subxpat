module abs_diff_i4_o3_lpp3_ppo3_pit6_et4_SOP1SHARELOGIC (in0, in1, in2, in3, out0, out1);
// declaring inputs
input in0,  in1,  in2,  in3;
// declaring outputs
output out0,  out1;
// JSON model input
wire w_in3, w_in2, w_in1, w_in0;
// JSON model output
wire w_g17, w_g21;
//json model
wire w_g17_pr, w_g21_pr, w_pr0_o0, w_pr1_o0, w_pr2_o0, w_pr3_o0, w_pr4_o0, w_pr5_o0, w_pr0_o1, w_pr1_o1, w_pr2_o1, w_pr3_o1, w_pr4_o1, w_pr5_o1, w_pr0, w_pr1, w_pr2, w_pr3, w_pr4, w_pr5;
// JSON model input assign
assign w_in3 = in3;
assign w_in2 = in2;
assign w_in1 = in1;
assign w_in0 = in0;

//json model assigns (approximated Shared/XPAT part)
//assign literals to products
assign w_pr0 = w_in2 & w_in3;
assign w_pr1 = w_in1 & w_in3;
assign w_pr2 = ~w_in1;
assign w_pr3 = w_in0;
assign w_pr4 = ~w_in0;
assign w_pr5 = 1;
//if a product has literals and if the product is being "activated" for that output
assign w_pr0_o0 = w_pr0 & 1;
assign w_pr1_o0 = w_pr1 & 1;
assign w_pr2_o0 = w_pr2 & 1;
assign w_pr3_o0 = w_pr3 & 1;
assign w_pr4_o0 = w_pr4 & 0;
assign w_pr5_o0 = w_pr5 & 0;
assign w_pr0_o1 = w_pr0 & 0;
assign w_pr1_o1 = w_pr1 & 0;
assign w_pr2_o1 = w_pr2 & 0;
assign w_pr3_o1 = w_pr3 & 0;
assign w_pr4_o1 = w_pr4 & 1;
assign w_pr5_o1 = w_pr5 & 1;
//compose an output with corresponding products (OR)
assign w_g17 = w_pr0_o0 | w_pr1_o0 | w_pr2_o0 | w_pr3_o0 | w_pr4_o0 | w_pr5_o0;
assign w_g21 = w_pr0_o1 | w_pr1_o1 | w_pr2_o1 | w_pr3_o1 | w_pr4_o1 | w_pr5_o1;
//if an output has products and if it is part of the JSON model
assign w_g17_pr = w_g17 & 1;
assign w_g21_pr = w_g21 & 1;
// output assigns
assign out0 = w_g17_pr;
assign out1 = w_g21_pr;
endmodule