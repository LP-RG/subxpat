module abs_diff_i208_o104(a,b,r);
input [103:0] a,b;
output [103:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
