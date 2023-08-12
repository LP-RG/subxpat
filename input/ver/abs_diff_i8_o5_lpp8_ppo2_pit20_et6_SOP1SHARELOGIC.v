module abs_diff_i8_o5_lpp8_ppo2_pit20_et6_SOP1SHARELOGIC (in0, in1, in2, in3, in4, in5, in6, in7, out0, out1, out2, out3);
// declaring inputs
input in0,  in1,  in2,  in3,  in4,  in5,  in6,  in7;
// declaring outputs
output out0,  out1,  out2,  out3;
// JSON model input
wire w_in7, w_in6, w_in5, w_in4, w_in3, w_in2, w_in1, w_in0;
// JSON model output
wire w_g36, w_g66, w_g104, w_g105;
//json model
wire w_g36_pr, w_g66_pr, w_g104_pr, w_g105_pr, w_pr0_o0, w_pr1_o0, w_pr2_o0, w_pr3_o0, w_pr4_o0, w_pr5_o0, w_pr6_o0, w_pr7_o0, w_pr8_o0, w_pr9_o0, w_pr10_o0, w_pr11_o0, w_pr12_o0, w_pr13_o0, w_pr14_o0, w_pr15_o0, w_pr16_o0, w_pr17_o0, w_pr18_o0, w_pr19_o0, w_pr0_o1, w_pr1_o1, w_pr2_o1, w_pr3_o1, w_pr4_o1, w_pr5_o1, w_pr6_o1, w_pr7_o1, w_pr8_o1, w_pr9_o1, w_pr10_o1, w_pr11_o1, w_pr12_o1, w_pr13_o1, w_pr14_o1, w_pr15_o1, w_pr16_o1, w_pr17_o1, w_pr18_o1, w_pr19_o1, w_pr0_o2, w_pr1_o2, w_pr2_o2, w_pr3_o2, w_pr4_o2, w_pr5_o2, w_pr6_o2, w_pr7_o2, w_pr8_o2, w_pr9_o2, w_pr10_o2, w_pr11_o2, w_pr12_o2, w_pr13_o2, w_pr14_o2, w_pr15_o2, w_pr16_o2, w_pr17_o2, w_pr18_o2, w_pr19_o2, w_pr0_o3, w_pr1_o3, w_pr2_o3, w_pr3_o3, w_pr4_o3, w_pr5_o3, w_pr6_o3, w_pr7_o3, w_pr8_o3, w_pr9_o3, w_pr10_o3, w_pr11_o3, w_pr12_o3, w_pr13_o3, w_pr14_o3, w_pr15_o3, w_pr16_o3, w_pr17_o3, w_pr18_o3, w_pr19_o3, w_pr0, w_pr1, w_pr2, w_pr3, w_pr4, w_pr5, w_pr6, w_pr7, w_pr8, w_pr9, w_pr10, w_pr11, w_pr12, w_pr13, w_pr14, w_pr15, w_pr16, w_pr17, w_pr18, w_pr19;
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
assign w_pr0 = ~w_in0 & w_in1 & ~w_in2 & ~w_in3 & ~w_in4 & w_in5 & w_in6 & w_in7;
assign w_pr1 = w_in1 & ~w_in2 & ~w_in3 & ~w_in4 & w_in5 & w_in6 & w_in7;
assign w_pr2 = ~w_in0 & w_in1 & ~w_in3 & ~w_in4 & w_in5 & w_in6 & w_in7;
assign w_pr3 = ~w_in0 & ~w_in3 & ~w_in4 & w_in5 & w_in6 & w_in7;
assign w_pr4 = ~w_in3 & ~w_in4 & w_in5 & w_in6 & w_in7;
assign w_pr5 = ~w_in0 & w_in1 & ~w_in2 & ~w_in4 & w_in5 & w_in6 & w_in7;
assign w_pr6 = w_in1 & ~w_in2 & ~w_in4 & w_in5 & w_in6 & w_in7;
assign w_pr7 = ~w_in0 & w_in1 & ~w_in4 & w_in5 & w_in6 & w_in7;
assign w_pr8 = w_in1 & ~w_in4 & w_in5 & w_in6 & w_in7;
assign w_pr9 = ~w_in0 & ~w_in4 & w_in5 & w_in6 & w_in7;
assign w_pr10 = ~w_in4 & w_in5 & w_in6 & w_in7;
assign w_pr11 = ~w_in0 & ~w_in3 & w_in5 & w_in6 & w_in7;
assign w_pr12 = ~w_in3 & w_in5 & w_in6 & w_in7;
assign w_pr13 = ~w_in0 & w_in5 & w_in6 & w_in7;
assign w_pr14 = ~w_in1 & ~w_in2 & ~w_in3 & ~w_in4 & ~w_in5 & w_in6 & w_in7;
assign w_pr15 = ~w_in0 & ~w_in1 & ~w_in2 & ~w_in3 & ~w_in5 & w_in6 & w_in7;
assign w_pr16 = ~w_in1 & ~w_in2 & ~w_in3 & ~w_in5 & w_in6 & w_in7;
assign w_pr17 = w_in7;
assign w_pr18 = w_in2 & w_in3 & ~w_in6 & ~w_in7;
assign w_pr19 = ~w_in7;
//if a product has literals and if the product is being "activated" for that output
assign w_pr0_o0 = w_pr0 & 0;
assign w_pr1_o0 = w_pr1 & 0;
assign w_pr2_o0 = w_pr2 & 0;
assign w_pr3_o0 = w_pr3 & 0;
assign w_pr4_o0 = w_pr4 & 0;
assign w_pr5_o0 = w_pr5 & 0;
assign w_pr6_o0 = w_pr6 & 0;
assign w_pr7_o0 = w_pr7 & 0;
assign w_pr8_o0 = w_pr8 & 0;
assign w_pr9_o0 = w_pr9 & 0;
assign w_pr10_o0 = w_pr10 & 0;
assign w_pr11_o0 = w_pr11 & 0;
assign w_pr12_o0 = w_pr12 & 0;
assign w_pr13_o0 = w_pr13 & 0;
assign w_pr14_o0 = w_pr14 & 0;
assign w_pr15_o0 = w_pr15 & 0;
assign w_pr16_o0 = w_pr16 & 0;
assign w_pr17_o0 = w_pr17 & 1;
assign w_pr18_o0 = w_pr18 & 0;
assign w_pr19_o0 = w_pr19 & 1;
assign w_pr0_o1 = w_pr0 & 0;
assign w_pr1_o1 = w_pr1 & 0;
assign w_pr2_o1 = w_pr2 & 0;
assign w_pr3_o1 = w_pr3 & 0;
assign w_pr4_o1 = w_pr4 & 0;
assign w_pr5_o1 = w_pr5 & 0;
assign w_pr6_o1 = w_pr6 & 0;
assign w_pr7_o1 = w_pr7 & 0;
assign w_pr8_o1 = w_pr8 & 0;
assign w_pr9_o1 = w_pr9 & 0;
assign w_pr10_o1 = w_pr10 & 0;
assign w_pr11_o1 = w_pr11 & 0;
assign w_pr12_o1 = w_pr12 & 0;
assign w_pr13_o1 = w_pr13 & 0;
assign w_pr14_o1 = w_pr14 & 0;
assign w_pr15_o1 = w_pr15 & 0;
assign w_pr16_o1 = w_pr16 & 0;
assign w_pr17_o1 = w_pr17 & 0;
assign w_pr18_o1 = w_pr18 & 0;
assign w_pr19_o1 = w_pr19 & 0;
assign w_pr0_o2 = w_pr0 & 1;
assign w_pr1_o2 = w_pr1 & 1;
assign w_pr2_o2 = w_pr2 & 1;
assign w_pr3_o2 = w_pr3 & 1;
assign w_pr4_o2 = w_pr4 & 1;
assign w_pr5_o2 = w_pr5 & 1;
assign w_pr6_o2 = w_pr6 & 1;
assign w_pr7_o2 = w_pr7 & 1;
assign w_pr8_o2 = w_pr8 & 1;
assign w_pr9_o2 = w_pr9 & 1;
assign w_pr10_o2 = w_pr10 & 1;
assign w_pr11_o2 = w_pr11 & 1;
assign w_pr12_o2 = w_pr12 & 1;
assign w_pr13_o2 = w_pr13 & 1;
assign w_pr14_o2 = w_pr14 & 0;
assign w_pr15_o2 = w_pr15 & 0;
assign w_pr16_o2 = w_pr16 & 0;
assign w_pr17_o2 = w_pr17 & 1;
assign w_pr18_o2 = w_pr18 & 0;
assign w_pr19_o2 = w_pr19 & 1;
assign w_pr0_o3 = w_pr0 & 0;
assign w_pr1_o3 = w_pr1 & 0;
assign w_pr2_o3 = w_pr2 & 0;
assign w_pr3_o3 = w_pr3 & 0;
assign w_pr4_o3 = w_pr4 & 1;
assign w_pr5_o3 = w_pr5 & 0;
assign w_pr6_o3 = w_pr6 & 0;
assign w_pr7_o3 = w_pr7 & 0;
assign w_pr8_o3 = w_pr8 & 0;
assign w_pr9_o3 = w_pr9 & 0;
assign w_pr10_o3 = w_pr10 & 0;
assign w_pr11_o3 = w_pr11 & 1;
assign w_pr12_o3 = w_pr12 & 1;
assign w_pr13_o3 = w_pr13 & 0;
assign w_pr14_o3 = w_pr14 & 1;
assign w_pr15_o3 = w_pr15 & 1;
assign w_pr16_o3 = w_pr16 & 1;
assign w_pr17_o3 = w_pr17 & 0;
assign w_pr18_o3 = w_pr18 & 1;
assign w_pr19_o3 = w_pr19 & 0;
//compose an output with corresponding products (OR)
assign w_g36 = w_pr0_o0 | w_pr1_o0 | w_pr2_o0 | w_pr3_o0 | w_pr4_o0 | w_pr5_o0 | w_pr6_o0 | w_pr7_o0 | w_pr8_o0 | w_pr9_o0 | w_pr10_o0 | w_pr11_o0 | w_pr12_o0 | w_pr13_o0 | w_pr14_o0 | w_pr15_o0 | w_pr16_o0 | w_pr17_o0 | w_pr18_o0 | w_pr19_o0;
assign w_g105 = w_pr0_o1 | w_pr1_o1 | w_pr2_o1 | w_pr3_o1 | w_pr4_o1 | w_pr5_o1 | w_pr6_o1 | w_pr7_o1 | w_pr8_o1 | w_pr9_o1 | w_pr10_o1 | w_pr11_o1 | w_pr12_o1 | w_pr13_o1 | w_pr14_o1 | w_pr15_o1 | w_pr16_o1 | w_pr17_o1 | w_pr18_o1 | w_pr19_o1;
assign w_g104 = w_pr0_o2 | w_pr1_o2 | w_pr2_o2 | w_pr3_o2 | w_pr4_o2 | w_pr5_o2 | w_pr6_o2 | w_pr7_o2 | w_pr8_o2 | w_pr9_o2 | w_pr10_o2 | w_pr11_o2 | w_pr12_o2 | w_pr13_o2 | w_pr14_o2 | w_pr15_o2 | w_pr16_o2 | w_pr17_o2 | w_pr18_o2 | w_pr19_o2;
assign w_g66 = w_pr0_o3 | w_pr1_o3 | w_pr2_o3 | w_pr3_o3 | w_pr4_o3 | w_pr5_o3 | w_pr6_o3 | w_pr7_o3 | w_pr8_o3 | w_pr9_o3 | w_pr10_o3 | w_pr11_o3 | w_pr12_o3 | w_pr13_o3 | w_pr14_o3 | w_pr15_o3 | w_pr16_o3 | w_pr17_o3 | w_pr18_o3 | w_pr19_o3;
//if an output has products and if it is part of the JSON model
assign w_g36_pr = w_g36 & 1;
assign w_g66_pr = w_g66 & 1;
assign w_g104_pr = w_g104 & 1;
assign w_g105_pr = w_g105 & 0;
// output assigns
assign out0 = w_g36_pr;
assign out3 = w_g66_pr;
assign out2 = w_g104_pr;
assign out1 = w_g105_pr;
endmodule