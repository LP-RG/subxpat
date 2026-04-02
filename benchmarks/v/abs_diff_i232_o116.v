module abs_diff_i232_o116(a,b,r);
input [115:0] a,b;
output [115:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
