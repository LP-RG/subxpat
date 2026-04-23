module abs_diff_i448_o224(a,b,r);
input [223:0] a,b;
output [223:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
