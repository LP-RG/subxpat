module adder_i4_o3_lpp2_ppo2_pit1_et3_SOP1SHARELOGIC (in0, in1, in2, in3, out0, out1, out2);
// declaring inputs
input in0,  in1,  in2,  in3;
// declaring outputs
output out0,  out1,  out2;
// JSON model input
wire w_in3, w_in2, w_in1, w_in0;
// JSON model output
wire w_g19, w_g26, w_g27;
//json model
wire w_g19_pr, w_g26_pr, w_g27_pr, w_pr0_o0, w_pr0_o1, w_pr0_o2, w_pr0;
// JSON model input assign
assign w_in3 = in3;
assign w_in2 = in2;
assign w_in1 = in1;
assign w_in0 = in0;

//json model assigns (approximated Shared/XPAT part)
//assign literals to products
assign w_pr0 = 1;
//if a product has literals and if the product is being "activated" for that output
assign w_pr0_o0 = w_pr0 & 1;
assign w_pr0_o1 = w_pr0 & 1;
assign w_pr0_o2 = w_pr0 & 0;
//compose an output with corresponding products (OR)
assign w_g19 = w_pr0_o0;
assign w_g27 = w_pr0_o1;
assign w_g26 = w_pr0_o2;
//if an output has products and if it is part of the JSON model
assign w_g19_pr = w_g19 & 1;
assign w_g26_pr = w_g26 & 0;
assign w_g27_pr = w_g27 & 1;
// output assigns
assign out0 = w_g19_pr;
assign out2 = w_g26_pr;
assign out1 = w_g27_pr;
endmodule