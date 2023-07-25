module abs_diff_i4_o3_lpp4_ppo2_pit3_et2_SOP1SHARELOGIC (in0, in1, in2, in3, out0, out1);
// declaring inputs
//COPY
input in0,  in1,  in2,  in3;
// declaring outputs
output out0,  out1;
// JSON model input
wire w_in3, w_in2, w_in1, w_in0;
// JSON model output
wire w_g17, w_g21;


//json model
wire p_pr0, p_pr1, p_pr2;
wire p_pr0_o0, p_pr1_o0, p_pr2_o0, p_pr0_o1, p_pr1_o1, p_pr2_o1;
wire w_g17_pr, w_g21_pr;


// JSON model input assign
assign w_in3 = in3;
assign w_in2 = in2;
assign w_in1 = in1;
assign w_in0 = in0;
//json model assigns (approximated Shared/XPAT part)
assign p_pr0 = w_in1 & ~w_in3;
assign p_pr1 = ~w_in1 & w_in2;
assign p_pr2 = 0;

//assign product to output
assign p_pr0_o0 = p_pr0 & 1 | 0 (if en la variable de asignado o no)
///...

//assign products to output, at least one should be used
assign w_g17 = p_pr0_o0 | p_pr1_o0 | p_pr2_o0;
assign w_g21 = p_pr0_o1 | p_pr1_o1 | p_pr2_o1;

//assign products to activated output
assign w_g17_pr = w_g17 & p_o1 (if the output is activated or not)

// output assigns
assign out0 = w_g17_pr;
assign out1 = w_g21_pr;
endmodule