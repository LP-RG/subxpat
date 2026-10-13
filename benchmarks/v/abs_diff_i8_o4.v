module top (a,b,r);
input [3:0] a,b;
output [3:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
