module abs_diff_i544_o272(a,b,r);
input [271:0] a,b;
output [271:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
