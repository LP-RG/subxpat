module abs_diff_i8_o5_lpp3_ppo5_pit4_et6_SOP1SHARELOGIC (in0, in1, in2, in3, in4, in5, in6, in7, out0, out1, out2, out3);
// declaring inputs
input in0,  in1,  in2,  in3,  in4,  in5,  in6,  in7;
// declaring outputs
output out0,  out1,  out2,  out3;
// JSON model input
wire w_in7, w_in6, w_in5, w_in4, w_in3, w_in2, w_in1, w_in0;
// JSON model output
wire w_g36, w_g66, w_g104, w_g105;
//json model
wire w_g36_pr, w_g66_pr, w_g104_pr, w_g105_pr, w_pr0_o0, w_pr1_o0, w_pr2_o0, w_pr3_o0, w_pr0_o1, w_pr1_o1, w_pr2_o1, w_pr3_o1, w_pr0_o2, w_pr1_o2, w_pr2_o2, w_pr3_o2, w_pr0_o3, w_pr1_o3, w_pr2_o3, w_pr3_o3, w_pr0, w_pr1, w_pr2, w_pr3;
// JSON model input assign
assign w_in7 = in7;
assign w_in6 = in6;
assign w_in5 = in5;
assign w_in4 = in4;
assign w_in3 = in3;
assign w_in2 = in2;
assign w_in1 = in1;
assign w_in0 = in0;

//json model assigns (approximated Shared/XPAT part)
//assign literals to products
assign w_pr0 = ~w_in2 & ~w_in3 & w_in7;
assign w_pr1 = w_in3 & ~w_in6 & ~w_in7;
assign w_pr2 = w_in6;
assign w_pr3 = w_in2 & ~w_in6;
//if a product has literals and if the product is being "activated" for that output
assign w_pr0_o0 = w_pr0 & 1;
assign w_pr1_o0 = w_pr1 & 1;
assign w_pr2_o0 = w_pr2 & 0;
assign w_pr3_o0 = w_pr3 & 1;
assign w_pr0_o1 = w_pr0 & 1;
assign w_pr1_o1 = w_pr1 & 1;
assign w_pr2_o1 = w_pr2 & 1;
assign w_pr3_o1 = w_pr3 & 1;
assign w_pr0_o2 = w_pr0 & 0;
assign w_pr1_o2 = w_pr1 & 0;
assign w_pr2_o2 = w_pr2 & 1;
assign w_pr3_o2 = w_pr3 & 1;
assign w_pr0_o3 = w_pr0 & 1;
assign w_pr1_o3 = w_pr1 & 1;
assign w_pr2_o3 = w_pr2 & 0;
assign w_pr3_o3 = w_pr3 & 0;
//compose an output with corresponding products (OR)
assign w_g36 = w_pr0_o0 | w_pr1_o0 | w_pr2_o0 | w_pr3_o0;
assign w_g105 = w_pr0_o1 | w_pr1_o1 | w_pr2_o1 | w_pr3_o1;
assign w_g104 = w_pr0_o2 | w_pr1_o2 | w_pr2_o2 | w_pr3_o2;
assign w_g66 = w_pr0_o3 | w_pr1_o3 | w_pr2_o3 | w_pr3_o3;
//if an output has products and if it is part of the JSON model
assign w_g36_pr = w_g36 & 1;
assign w_g66_pr = w_g66 & 1;
assign w_g104_pr = w_g104 & 1;
assign w_g105_pr = w_g105 & 1;
// output assigns
assign out0 = w_g36_pr;
assign out3 = w_g66_pr;
assign out2 = w_g104_pr;
assign out1 = w_g105_pr;
endmodule