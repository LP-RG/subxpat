module mul_i4_o4_lpp0_ppo4_et8_SOP1 (in0, in1, in2, in3, out0, out1, out2, out3);
//input/output declarations
input in0, in1, in2, in3;
output out0, out1, out2, out3;
//intact gates wires 
	//no intact gates detected!
//annotated subgraph inputs
wire w_in3, w_in2, w_in1, w_in0;
//annotated subgraph outputs
wire w_g3, w_g6, w_g10, w_g12;
// no json wires!
//json model
wire p_o0_t0, p_o0_t1, p_o0_t2, p_o0_t3, p_o1_t0, p_o1_t1, p_o1_t2, p_o1_t3, p_o2_t0, p_o2_t1, p_o2_t2, p_o2_t3, p_o3_t0, p_o3_t1, p_o3_t2, p_o3_t3;
//subgraph inputs assigns
assign w_in3 = in3;
assign w_in2 = in2;
assign w_in1 = in1;
assign w_in0 = in0;
//mapping subgraph inputs to json inputs
//json model assigns (approximated/XPATed part)
assign w_g3 = 0;
assign w_g6 = 0;
assign w_g10 = 0;
assign p_o3_t0 = 1;
assign p_o3_t1 = 1;
assign p_o3_t2 = 1;
assign p_o3_t3 = 1;
assign w_g12 = p_o3_t0 | p_o3_t1 | p_o3_t2 | p_o3_t3;
// intact gates assigns
// output assigns
assign out0 = w_g3;
assign out1 = w_g12;
assign out2 = w_g10;
assign out3 = w_g6;
endmodule