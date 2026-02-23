module abs_diff_i536_o268(a,b,r);
input [267:0] a,b;
output [267:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
