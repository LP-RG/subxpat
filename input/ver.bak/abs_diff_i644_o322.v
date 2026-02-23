module abs_diff_i644_o322(a,b,r);
input [321:0] a,b;
output [321:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
