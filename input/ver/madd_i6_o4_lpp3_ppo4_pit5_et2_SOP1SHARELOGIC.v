module madd_i6_o4_lpp3_ppo4_pit5_et2_SOP1SHARELOGIC (in0, in1, in2, in3, in4, in5, out0, out1, out2, out3);
// declaring inputs
input in0,  in1,  in2,  in3,  in4,  in5;
// declaring outputs
output out0,  out1,  out2,  out3;
// JSON model input
wire w_in5, w_in4, w_in3, w_in2, w_in1, w_in0;
// JSON model output
wire w_g29, w_g46, w_g52, w_g54;
//json model
wire w_g29_pr, w_g46_pr, w_g52_pr, w_g54_pr, w_pr0_o0, w_pr1_o0, w_pr2_o0, w_pr3_o0, w_pr4_o0, w_pr0_o1, w_pr1_o1, w_pr2_o1, w_pr3_o1, w_pr4_o1, w_pr0_o2, w_pr1_o2, w_pr2_o2, w_pr3_o2, w_pr4_o2, w_pr0_o3, w_pr1_o3, w_pr2_o3, w_pr3_o3, w_pr4_o3, w_pr0, w_pr1, w_pr2, w_pr3, w_pr4;
// JSON model input assign
assign w_in5 = in5;
assign w_in4 = in4;
assign w_in3 = in3;
assign w_in2 = in2;
assign w_in1 = in1;
assign w_in0 = in0;

//json model assigns (approximated Shared/XPAT part)
//assign literals to products
assign w_pr0 = w_in5;
assign w_pr1 = w_in0 & w_in1 & w_in3;
assign w_pr2 = ~w_in0 & w_in1 & w_in3;
assign w_pr3 = w_in0 & ~w_in1 & w_in3;
assign w_pr4 = w_in1 & w_in2 & ~w_in3;
//if a product has literals and if the product is being "activated" for that output
assign w_pr0_o0 = w_pr0 & 0;
assign w_pr1_o0 = w_pr1 & 0;
assign w_pr2_o0 = w_pr2 & 1;
assign w_pr3_o0 = w_pr3 & 0;
assign w_pr4_o0 = w_pr4 & 0;
assign w_pr0_o1 = w_pr0 & 1;
assign w_pr1_o1 = w_pr1 & 0;
assign w_pr2_o1 = w_pr2 & 0;
assign w_pr3_o1 = w_pr3 & 0;
assign w_pr4_o1 = w_pr4 & 0;
assign w_pr0_o2 = w_pr0 & 0;
assign w_pr1_o2 = w_pr1 & 0;
assign w_pr2_o2 = w_pr2 & 1;
assign w_pr3_o2 = w_pr3 & 1;
assign w_pr4_o2 = w_pr4 & 1;
assign w_pr0_o3 = w_pr0 & 0;
assign w_pr1_o3 = w_pr1 & 1;
assign w_pr2_o3 = w_pr2 & 0;
assign w_pr3_o3 = w_pr3 & 0;
assign w_pr4_o3 = w_pr4 & 0;
//compose an output with corresponding products (OR)
assign w_g29 = w_pr0_o0 | w_pr1_o0 | w_pr2_o0 | w_pr3_o0 | w_pr4_o0;
assign w_g52 = w_pr0_o1 | w_pr1_o1 | w_pr2_o1 | w_pr3_o1 | w_pr4_o1;
assign w_g54 = w_pr0_o2 | w_pr1_o2 | w_pr2_o2 | w_pr3_o2 | w_pr4_o2;
assign w_g46 = w_pr0_o3 | w_pr1_o3 | w_pr2_o3 | w_pr3_o3 | w_pr4_o3;
//if an output has products and if it is part of the JSON model
assign w_g29_pr = w_g29 & 1;
assign w_g46_pr = w_g46 & 1;
assign w_g52_pr = w_g52 & 1;
assign w_g54_pr = w_g54 & 1;
// output assigns
assign out0 = w_g29_pr;
assign out3 = w_g46_pr;
assign out1 = w_g52_pr;
assign out2 = w_g54_pr;
endmodule