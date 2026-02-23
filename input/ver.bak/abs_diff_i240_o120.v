module abs_diff_i240_o120(a,b,r);
input [119:0] a,b;
output [119:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
