module abs_diff_i860_o430(a,b,r);
input [429:0] a,b;
output [429:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
