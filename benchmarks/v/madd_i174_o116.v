module madd_i174_o116 (a, b, c, r);
input [57:0] a,b,c;
output [115:0] r;

assign r = (a * b) + c;

endmodule
