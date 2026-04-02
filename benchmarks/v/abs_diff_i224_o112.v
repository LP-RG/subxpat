module abs_diff_i224_o112(a,b,r);
input [111:0] a,b;
output [111:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
