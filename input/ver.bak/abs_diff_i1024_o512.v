module abs_diff_i1024_o512(a,b,r);
input [511:0] a,b;
output [511:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
