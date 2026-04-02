module abs_diff_i880_o440(a,b,r);
input [439:0] a,b;
output [439:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
