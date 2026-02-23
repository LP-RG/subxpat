module abs_diff_i204_o102(a,b,r);
input [101:0] a,b;
output [101:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
