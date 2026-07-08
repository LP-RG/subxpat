module top (a,b,r);
input [9:0] a,b;
output [9:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
