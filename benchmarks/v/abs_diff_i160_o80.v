module abs_diff_i160_o80(a,b,r);
input [79:0] a,b;
output [79:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
